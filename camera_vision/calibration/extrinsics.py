from __future__ import annotations

import cv2
import numpy as np

from camera_vision.calibration.intrinsics import CharucoBoardSpec


class ExtrinsicsCalibrator:
    """Collects simultaneous ChArUco observations from both cameras, then runs stereo calibration.

    Caller provides previously computed intrinsics (K, dist) for each camera.
    """

    def __init__(
        self,
        spec: CharucoBoardSpec,
        K_left: np.ndarray,
        dist_left: np.ndarray,
        K_right: np.ndarray,
        dist_right: np.ndarray,
    ) -> None:
        self._spec = spec
        self._aruco_dict, self._board = spec.build()
        self._detector = cv2.aruco.CharucoDetector(self._board)
        self._K_l = K_left
        self._d_l = dist_left
        self._K_r = K_right
        self._d_r = dist_right
        self._obj_points: list[np.ndarray] = []
        self._img_points_l: list[np.ndarray] = []
        self._img_points_r: list[np.ndarray] = []
        self._image_size: tuple[int, int] | None = None

    @property
    def n_captures(self) -> int:
        return len(self._obj_points)

    def _detect_pair(self, left: np.ndarray, right: np.ndarray):
        gl = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        gr = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
        cl, il, _, _ = self._detector.detectBoard(gl)
        cr, ir, _, _ = self._detector.detectBoard(gr)
        return cl, il, cr, ir

    def observe(self, left: np.ndarray, right: np.ndarray) -> bool:
        if left.shape[:2] != right.shape[:2]:
            raise ValueError("Left and right frames must have the same shape")
        cl, il, cr, ir = self._detect_pair(left, right)
        if cl is None or il is None or cr is None or ir is None:
            return False
        common_ids = np.intersect1d(il.flatten(), ir.flatten())
        if len(common_ids) < 6:
            return False

        def select(corners, ids, wanted):
            flat = ids.flatten()
            mask = np.isin(flat, wanted)
            return corners[mask]

        cl_sel = select(cl, il, common_ids)
        cr_sel = select(cr, ir, common_ids)
        ids_sel = common_ids.reshape(-1, 1).astype(np.int32)
        op, _ = self._board.matchImagePoints(cl_sel, ids_sel)
        _, ip_l = self._board.matchImagePoints(cl_sel, ids_sel)
        _, ip_r = self._board.matchImagePoints(cr_sel, ids_sel)
        if op is None or ip_l is None or ip_r is None:
            return False

        h, w = left.shape[:2]
        if self._image_size is None:
            self._image_size = (w, h)

        self._obj_points.append(op)
        self._img_points_l.append(ip_l)
        self._img_points_r.append(ip_r)
        return True

    def calibrate(self) -> dict:
        if self.n_captures < 3:
            raise RuntimeError("Need at least 3 stereo captures")
        assert self._image_size is not None

        flags = cv2.CALIB_FIX_INTRINSIC
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)

        rms, _, _, _, _, R, T, E, F = cv2.stereoCalibrate(
            self._obj_points,
            self._img_points_l,
            self._img_points_r,
            self._K_l,
            self._d_l,
            self._K_r,
            self._d_r,
            self._image_size,
            criteria=criteria,
            flags=flags,
        )

        _, _, _, _, Q, _, _ = cv2.stereoRectify(
            self._K_l, self._d_l, self._K_r, self._d_r, self._image_size, R, T
        )

        return {
            "rms": float(rms),
            "R": R,
            "T": T,
            "E": E,
            "F": F,
            "Q": Q,
            "image_size": self._image_size,
        }
