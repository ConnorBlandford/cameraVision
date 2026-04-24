from __future__ import annotations

import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np
from flask import (
    Flask,
    Response,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
)

from camera_vision.calibration import (
    CharucoBoardSpec,
    ExtrinsicsCalibrator,
    IntrinsicsCalibrator,
    inspect_state,
    load_intrinsics,
    save_extrinsics,
    save_intrinsics,
)
from camera_vision.detection import (
    draw_detections,
    draw_targets,
    get_detector,
    resolve_target_class,
)
from camera_vision.manifest import DetectionRound, ManifestStore, RoundStatus
from camera_vision.sources import build_source, CameraSource


# -----------------------------------------------------------------------------
# Shared resources (per-app, lazy)
# -----------------------------------------------------------------------------

_camera_lock = threading.Lock()
_camera: CameraSource | None = None

_intrinsics_sessions: dict[str, IntrinsicsCalibrator] = {}
_extrinsics_session: dict[str, ExtrinsicsCalibrator] = {}

_manifest_store: ManifestStore | None = None


def _paths() -> dict:
    cfg = current_app.config["CAMERA_VISION_CONFIG"]
    root: Path = current_app.config["CAMERA_VISION_ROOT"]
    return {k: (root / v) for k, v in cfg["paths"].items()}


def _get_camera() -> CameraSource:
    global _camera
    with _camera_lock:
        if _camera is None:
            cfg = current_app.config["CAMERA_VISION_CONFIG"]
            src = build_source(cfg)
            src.open()
            _camera = src
        return _camera


def _get_manifest() -> ManifestStore:
    global _manifest_store
    if _manifest_store is None:
        _manifest_store = ManifestStore(_paths()["manifest"])
    return _manifest_store


def _board_spec() -> CharucoBoardSpec:
    cfg = current_app.config["CAMERA_VISION_CONFIG"]["calibration"]["board"]
    return CharucoBoardSpec(**cfg)


def _encode_jpeg(bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise RuntimeError("JPEG encoding failed")
    return buf.tobytes()


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        state = inspect_state(_paths()["calibrations"])
        cam = _safe_camera_info()
        return render_template("index.html", state=state, camera=cam)

    @app.route("/api/status")
    def api_status():
        state = inspect_state(_paths()["calibrations"])
        return jsonify(
            {
                "intrinsics_ready": state.intrinsics_ready,
                "fully_calibrated": state.fully_calibrated,
                "intrinsics_left": asdict(state.intrinsics_left) | {"path": str(state.intrinsics_left.path)},
                "intrinsics_right": asdict(state.intrinsics_right) | {"path": str(state.intrinsics_right.path)},
                "extrinsics": asdict(state.extrinsics) | {"path": str(state.extrinsics.path)},
                "camera": _safe_camera_info(),
            }
        )

    # --- Calibration ---------------------------------------------------------

    @app.route("/calibration")
    def calibration():
        state = inspect_state(_paths()["calibrations"])
        return render_template("calibration.html", state=state)

    @app.route("/calibration/stream/raw/<side>")
    def calibration_stream_raw(side: str):
        if side not in ("left", "right"):
            abort(404)
        return Response(
            _mjpeg_stream(_frame_provider_raw(side)),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @app.route("/calibration/stream/charuco/<side>")
    def calibration_stream_charuco(side: str):
        if side not in ("left", "right"):
            abort(404)
        calibrator = _ensure_intrinsics_session(side)
        return Response(
            _mjpeg_stream(lambda: calibrator.annotate(_read_side(side))),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @app.route("/api/calibration/intrinsics/<side>/capture", methods=["POST"])
    def api_intrinsics_capture(side: str):
        if side not in ("left", "right"):
            abort(404)
        calibrator = _ensure_intrinsics_session(side)
        frame = _read_side(side)
        ok = calibrator.observe(frame)
        return jsonify({"accepted": ok, "n_captures": calibrator.n_captures})

    @app.route("/api/calibration/intrinsics/<side>/finalise", methods=["POST"])
    def api_intrinsics_finalise(side: str):
        if side not in ("left", "right"):
            abort(404)
        payload = request.get_json(silent=True) or {}
        user = (payload.get("user") or "").strip() or "unknown"
        calibrator = _intrinsics_sessions.get(side)
        if calibrator is None:
            abort(400, "No intrinsics session in progress")
        result = calibrator.calibrate()
        out_path = _paths()["calibrations"] / f"intrinsics-{side}.yaml"
        save_intrinsics(
            out_path,
            user=user,
            camera=side,
            image_size=result["image_size"],
            K=result["K"],
            dist=result["dist"],
            rms=result["rms"],
            n_captures=result["n_captures"],
        )
        _intrinsics_sessions.pop(side, None)
        return jsonify({"path": str(out_path), "rms": result["rms"], "n_captures": result["n_captures"]})

    @app.route("/api/calibration/intrinsics/<side>/reset", methods=["POST"])
    def api_intrinsics_reset(side: str):
        _intrinsics_sessions.pop(side, None)
        return jsonify({"ok": True})

    @app.route("/api/calibration/extrinsics/capture", methods=["POST"])
    def api_extrinsics_capture():
        cal = _ensure_extrinsics_session()
        if cal is None:
            abort(400, "Both intrinsics must be calibrated first")
        cam = _get_camera()
        frame = cam.read()
        ok = cal.observe(frame.left, frame.right)
        return jsonify({"accepted": ok, "n_captures": cal.n_captures})

    @app.route("/api/calibration/extrinsics/finalise", methods=["POST"])
    def api_extrinsics_finalise():
        payload = request.get_json(silent=True) or {}
        user = (payload.get("user") or "").strip() or "unknown"
        cal = _extrinsics_session.get("cal")
        if cal is None:
            abort(400, "No extrinsics session in progress")
        result = cal.calibrate()
        out_path = _paths()["calibrations"] / "extrinsics.yaml"
        save_extrinsics(
            out_path,
            user=user,
            image_size=result["image_size"],
            R=result["R"],
            T=result["T"],
            E=result["E"],
            F=result["F"],
            Q=result["Q"],
            rms=result["rms"],
        )
        _extrinsics_session.pop("cal", None)
        return jsonify({"path": str(out_path), "rms": result["rms"]})

    @app.route("/api/calibration/extrinsics/reset", methods=["POST"])
    def api_extrinsics_reset():
        _extrinsics_session.pop("cal", None)
        return jsonify({"ok": True})

    # --- Detection -----------------------------------------------------------

    @app.route("/detection")
    def detection():
        store = _get_manifest()
        rounds = store.list_rounds()
        rounds.sort(key=lambda r: r.started_at, reverse=True)
        cfg = current_app.config["CAMERA_VISION_CONFIG"]["detection"]
        return render_template(
            "detection.html",
            rounds=rounds,
            default_confidence=cfg["default_confidence"],
        )

    @app.route("/api/detection/round", methods=["POST"])
    def api_start_round():
        payload = request.get_json(silent=True) or {}
        target_type = str(payload.get("target_type", "")).strip()
        try:
            confidence = float(payload.get("confidence", 0.5))
        except (TypeError, ValueError):
            abort(400, "Invalid confidence")
        if not target_type:
            abort(400, "target_type required")

        round_ = DetectionRound(target_type=target_type, confidence_threshold=confidence)
        resolved = resolve_target_class(target_type)
        round_.class_filter_applied = resolved is not None
        _get_manifest().append(round_)
        return jsonify(round_.to_dict())

    @app.route("/api/detection/round/<round_id>/scan", methods=["POST"])
    def api_scan(round_id: str):
        store = _get_manifest()
        round_ = store.get(round_id)
        if round_ is None:
            abort(404)
        cam = _get_camera()
        frame = cam.read()
        paths = _paths()
        raw_dir: Path = paths["scan_images"]
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / f"raw-{round_.target_type}-{round_.uuid}.jpg"
        cv2.imwrite(str(raw_path), frame.left)
        advanced = store.advance(
            round_id,
            RoundStatus.SCANNED,
            raw_path=str(raw_path.relative_to(current_app.config["CAMERA_VISION_ROOT"])),
        )
        return jsonify(advanced.to_dict())

    @app.route("/api/detection/round/<round_id>/detect", methods=["POST"])
    def api_detect(round_id: str):
        store = _get_manifest()
        round_ = store.get(round_id)
        if round_ is None:
            abort(404)
        if round_.raw_path is None:
            abort(400, "Scan not done yet")
        root: Path = current_app.config["CAMERA_VISION_ROOT"]
        bgr = cv2.imread(str(root / round_.raw_path))
        if bgr is None:
            abort(500, "Could not read raw image")

        cfg = current_app.config["CAMERA_VISION_CONFIG"]["detection"]
        detector = get_detector(cfg["model_size"])
        target_class = resolve_target_class(round_.target_type)
        detections = detector.detect(bgr, round_.confidence_threshold, target_class=target_class)

        ann = draw_detections(bgr, detections, target_type=round_.target_type)
        det_dir: Path = _paths()["detection_annotation"]
        det_dir.mkdir(parents=True, exist_ok=True)
        det_path = det_dir / f"detection-{round_.target_type}-{round_.uuid}.jpg"
        cv2.imwrite(str(det_path), ann)

        # Auto-preselect by (threshold + delta).
        selection_delta = float(cfg["selection_delta"])
        preselected = [
            i for i, d in enumerate(detections)
            if d.confidence >= round_.confidence_threshold + selection_delta
        ]

        round_.detections = [
            {
                "bbox": list(d.bbox_xyxy),
                "class_id": d.class_id,
                "class_name": d.class_name,
                "confidence": d.confidence,
                "preselected": i in preselected,
            }
            for i, d in enumerate(detections)
        ]
        round_.detection_path = str(det_path.relative_to(root))
        round_.advance(RoundStatus.DETECTIONS_MADE)
        store.update(round_)
        return jsonify(round_.to_dict())

    @app.route("/api/detection/round/<round_id>/select", methods=["POST"])
    def api_select(round_id: str):
        payload = request.get_json(silent=True) or {}
        selected = set(int(i) for i in payload.get("selected", []))
        store = _get_manifest()
        round_ = store.get(round_id)
        if round_ is None:
            abort(404)
        if round_.raw_path is None or not round_.detections:
            abort(400, "Detection step not done")
        root: Path = current_app.config["CAMERA_VISION_ROOT"]
        bgr = cv2.imread(str(root / round_.raw_path))
        if bgr is None:
            abort(500, "Could not read raw image")

        from camera_vision.detection.detector import Detection

        dets = [
            Detection(
                bbox_xyxy=tuple(d["bbox"]),
                class_id=int(d["class_id"]),
                class_name=str(d["class_name"]),
                confidence=float(d["confidence"]),
            )
            for d in round_.detections
        ]
        ann = draw_targets(bgr, dets, selected, target_type=round_.target_type)
        tgt_dir: Path = _paths()["target_annotation"]
        tgt_dir.mkdir(parents=True, exist_ok=True)
        tgt_path = tgt_dir / f"target-{round_.target_type}-{round_.uuid}.jpg"
        cv2.imwrite(str(tgt_path), ann)

        for i, d in enumerate(round_.detections):
            d["selected"] = i in selected

        round_.target_path = str(tgt_path.relative_to(root))
        round_.advance(RoundStatus.TARGETS_SELECTED)
        store.update(round_)
        return jsonify(round_.to_dict())

    @app.route("/api/detection/round/<round_id>")
    def api_round(round_id: str):
        round_ = _get_manifest().get(round_id)
        if round_ is None:
            abort(404)
        return jsonify(round_.to_dict())

    @app.route("/api/detection/round/<round_id>/cancel", methods=["POST"])
    def api_cancel(round_id: str):
        store = _get_manifest()
        round_ = store.get(round_id)
        if round_ is None:
            abort(404)
        advanced = store.advance(round_id, RoundStatus.CANCELLED)
        return jsonify(advanced.to_dict())

    # --- Depth ---------------------------------------------------------------

    @app.route("/depth")
    def depth():
        state = inspect_state(_paths()["calibrations"])
        return render_template("depth.html", state=state)

    # --- Data files ----------------------------------------------------------

    @app.route("/data/<path:subpath>")
    def data_file(subpath: str):
        root: Path = current_app.config["CAMERA_VISION_ROOT"]
        return send_from_directory(root / "data", subpath)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _safe_camera_info() -> dict:
    cfg = current_app.config["CAMERA_VISION_CONFIG"]["camera"]
    return {
        "source": cfg["source"],
        "is_stereo": cfg["source"] == "stereo_uvc",
    }


def _read_side(side: str) -> np.ndarray:
    frame = _get_camera().read()
    return frame.left if side == "left" else frame.right


def _frame_provider_raw(side: str):
    def _get() -> np.ndarray:
        return _read_side(side)

    return _get


def _ensure_intrinsics_session(side: str) -> IntrinsicsCalibrator:
    if side not in _intrinsics_sessions:
        _intrinsics_sessions[side] = IntrinsicsCalibrator(_board_spec())
    return _intrinsics_sessions[side]


def _ensure_extrinsics_session() -> ExtrinsicsCalibrator | None:
    if "cal" in _extrinsics_session:
        return _extrinsics_session["cal"]
    cal_dir = _paths()["calibrations"]
    left_path = cal_dir / "intrinsics-left.yaml"
    right_path = cal_dir / "intrinsics-right.yaml"
    if not left_path.exists() or not right_path.exists():
        return None
    left = load_intrinsics(left_path)
    right = load_intrinsics(right_path)
    cal = ExtrinsicsCalibrator(
        _board_spec(),
        K_left=left["K"],
        dist_left=left["dist"],
        K_right=right["K"],
        dist_right=right["dist"],
    )
    _extrinsics_session["cal"] = cal
    return cal


def _mjpeg_stream(producer) -> Iterator[bytes]:
    """Yield multipart JPEG frames at ~15 fps. Isolated so the camera lock is held briefly."""
    while True:
        try:
            frame = producer()
            jpeg = _encode_jpeg(frame)
        except Exception:
            time.sleep(0.2)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
            + jpeg + b"\r\n"
        )
        time.sleep(0.066)
