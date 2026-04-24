import cv2

from camera_vision.sources.base import CameraSource, StereoFrame


class StereoUVCSource(CameraSource):
    """Two independent UVC cameras captured in lock-step.

    Targets the Inno-maker U20CAM-10800P pair. Both devices are opened via
    OpenCV's default UVC backend; frames are grabbed then retrieved to keep
    capture times as close as possible.
    """

    def __init__(
        self,
        left_index: int,
        right_index: int,
        width: int = 1920,
        height: int = 1080,
    ) -> None:
        self._left_index = left_index
        self._right_index = right_index
        self._width = width
        self._height = height
        self._left: cv2.VideoCapture | None = None
        self._right: cv2.VideoCapture | None = None

    def _open_one(self, index: int) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open UVC camera at index {index}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        return cap

    def open(self) -> None:
        self._left = self._open_one(self._left_index)
        self._right = self._open_one(self._right_index)

    def read(self) -> StereoFrame:
        if self._left is None or self._right is None:
            raise RuntimeError("Stereo source not opened")
        self._left.grab()
        self._right.grab()
        ok_l, left = self._left.retrieve()
        ok_r, right = self._right.retrieve()
        if not ok_l or not ok_r or left is None or right is None:
            raise RuntimeError("Stereo read failed")
        return StereoFrame.now(left=left, right=right)

    def close(self) -> None:
        for cap in (self._left, self._right):
            if cap is not None:
                cap.release()
        self._left = None
        self._right = None

    @property
    def is_stereo(self) -> bool:
        return True
