from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class CharucoBoardSpec:
    squares_x: int
    squares_y: int
    square_length_m: float
    marker_length_m: float
    dictionary: str = "DICT_5X5_100"

    def build(self):
        dict_id = getattr(cv2.aruco, self.dictionary)
        aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
        board = cv2.aruco.CharucoBoard(
            (self.squares_x, self.squares_y),
            self.square_length_m,
            self.marker_length_m,
            aruco_dict,
        )
        return aruco_dict, board


class IntrinsicsCalibrator:
    """Collects ChArUco observations across multiple frames and runs single-camera calibration.

    Use like:
        cal = IntrinsicsCalibrator(spec)
        for frame in frames:
            cal.observe(frame)
        result = cal.calibrate()
    """

    def __init__(self, spec: CharucoBoardSpec) -> None:
        self._spec = spec
        self._aruco_dict, self._board = spec.build()
        self._detector = cv2.aruco.CharucoDetector(self._board)
        self._all_corners: list[np.ndarray] = []
        self._all_ids: list[np.ndarray] = []
        self._image_size: tuple[int, int] | None = None

    @property
    def n_captures(self) -> int:
        return len(self._all_corners)

    def detect(self, bgr: np.ndarray) -> tuple[np.ndarray | None, np.ndarray | None]:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        corners, ids, _, _ = self._detector.detectBoard(gray)
        return corners, ids

    def observe(self, bgr: np.ndarray) -> bool:
        corners, ids = self.detect(bgr)
        if corners is None or ids is None or len(corners) < 6:
            return False
        h, w = bgr.shape[:2]
        if self._image_size is None:
            self._image_size = (w, h)
        elif self._image_size != (w, h):
            raise ValueError("Inconsistent frame size across captures")
        self._all_corners.append(corners)
        self._all_ids.append(ids)
        return True

    def annotate(self, bgr: np.ndarray) -> np.ndarray:
        corners, ids = self.detect(bgr)
        out = bgr.copy()
        if corners is not None and ids is not None:
            cv2.aruco.drawDetectedCornersCharuco(out, corners, ids)
        return out

    def calibrate(self) -> dict:
        if self.n_captures < 3:
            raise RuntimeError("Need at least 3 captures to calibrate")
        assert self._image_size is not None

        obj_points: list[np.ndarray] = []
        img_points: list[np.ndarray] = []
        for corners, ids in zip(self._all_corners, self._all_ids):
            op, ip = self._board.matchImagePoints(corners, ids)
            if op is None or ip is None or len(op) < 4:
                continue
            obj_points.append(op)
            img_points.append(ip)

        if len(obj_points) < 3:
            raise RuntimeError("Too few valid captures after matching")

        rms, K, dist, _, _ = cv2.calibrateCamera(
            obj_points, img_points, self._image_size, None, None
        )
        return {
            "rms": float(rms),
            "K": K,
            "dist": dist,
            "image_size": self._image_size,
            "n_captures": self.n_captures,
        }
