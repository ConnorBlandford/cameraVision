"""RF-DETR wrapper. Apache-2.0 sizes (N/S/M/L) only — PML 1.0 XL/2XL are excluded."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from camera_vision.detection.classes import lookup_class_name, resolve_target_class

_ALLOWED_SIZES = {"nano", "small", "medium", "large"}


@dataclass(frozen=True)
class Detection:
    bbox_xyxy: tuple[float, float, float, float]
    class_id: int
    class_name: str
    confidence: float


class Detector:
    """Lazy RF-DETR wrapper. The heavy model import happens on first `detect`.

    Thread-safe initialisation; a single Flask worker shares one model instance.
    """

    def __init__(self, size: str = "nano") -> None:
        if size not in _ALLOWED_SIZES:
            raise ValueError(
                f"Detector size {size!r} not allowed (permissive licence requires one of {_ALLOWED_SIZES})"
            )
        self._size = size
        self._lock = threading.Lock()
        self._model = None

    def _ensure(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            self._model = _load_rfdetr(self._size)

    def detect(
        self,
        bgr: np.ndarray,
        confidence: float,
        target_class: str | None = None,
    ) -> list[Detection]:
        self._ensure()
        assert self._model is not None

        import cv2

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        from PIL import Image

        image = Image.fromarray(rgb)
        raw = self._model.predict(image, threshold=confidence)

        xyxy = np.asarray(raw.xyxy, dtype=float)
        class_ids = np.asarray(raw.class_id, dtype=int)
        confs = np.asarray(raw.confidence, dtype=float)

        detections: list[Detection] = []
        for box, cid, conf in zip(xyxy, class_ids, confs):
            name = lookup_class_name(int(cid))
            if target_class is not None and name != target_class:
                continue
            detections.append(
                Detection(
                    bbox_xyxy=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                    class_id=int(cid),
                    class_name=name,
                    confidence=float(conf),
                )
            )
        return detections


def _load_rfdetr(size: str):
    from rfdetr import RFDETRNano, RFDETRSmall, RFDETRMedium, RFDETRLarge

    cls = {
        "nano": RFDETRNano,
        "small": RFDETRSmall,
        "medium": RFDETRMedium,
        "large": RFDETRLarge,
    }[size]
    return cls()


@lru_cache(maxsize=4)
def get_detector(size: str = "nano") -> Detector:
    return Detector(size=size)


__all__ = ["Detector", "Detection", "get_detector", "resolve_target_class"]
