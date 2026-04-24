from __future__ import annotations

import cv2
import numpy as np

from camera_vision.detection.detector import Detection


def _fmt_confidence(c: float) -> str:
    # Two significant figures per spec.
    return f"{c:.2g}"


def _draw_box(
    image: np.ndarray,
    bbox: tuple[float, float, float, float],
    label: str,
    color: tuple[int, int, int],
    *,
    glyph: str | None = None,
) -> None:
    x1, y1, x2, y2 = (int(v) for v in bbox)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

    display = f"{glyph} {label}" if glyph else label
    (tw, th), baseline = cv2.getTextSize(display, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    pad = 4
    ty1 = max(0, y1 - th - baseline - pad * 2)
    cv2.rectangle(image, (x1, ty1), (x1 + tw + pad * 2, ty1 + th + baseline + pad * 2), color, -1)
    cv2.putText(
        image,
        display,
        (x1 + pad, ty1 + th + pad),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )


DETECTION_COLOR = (0, 165, 255)  # orange — readable on both themes, CB-safe
SELECTED_COLOR = (40, 150, 40)    # green, paired with a tick glyph
UNSELECTED_COLOR = (40, 40, 200)  # red-ish, paired with a cross glyph


def draw_detections(
    bgr: np.ndarray,
    detections: list[Detection],
    *,
    target_type: str,
) -> np.ndarray:
    out = bgr.copy()
    for d in detections:
        label = f"{target_type} {_fmt_confidence(d.confidence)}"
        _draw_box(out, d.bbox_xyxy, label, DETECTION_COLOR)
    return out


def draw_targets(
    bgr: np.ndarray,
    detections: list[Detection],
    selected_indices: set[int],
    *,
    target_type: str,
) -> np.ndarray:
    out = bgr.copy()
    for i, d in enumerate(detections):
        is_sel = i in selected_indices
        status = "selected" if is_sel else "not selected"
        label = f"{target_type} — {status}"
        color = SELECTED_COLOR if is_sel else UNSELECTED_COLOR
        glyph = "OK" if is_sel else "X"
        _draw_box(out, d.bbox_xyxy, label, color, glyph=glyph)
    return out
