import cv2

from camera_vision.sources.base import CameraSource, StereoFrame


class WebcamSource(CameraSource):
    """Single webcam presented as a stereo pair (left == right).

    Stand-in for the real U20CAM-10800P setup so downstream stereo code paths
    stay exercised during laptop-only development.
    """

    def __init__(self, device_index: int = 0, width: int = 1280, height: int = 720) -> None:
        self._device_index = device_index
        self._width = width
        self._height = height
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        cap = cv2.VideoCapture(self._device_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(self._device_index)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open webcam at index {self._device_index}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._cap = cap

    def read(self) -> StereoFrame:
        if self._cap is None:
            raise RuntimeError("Webcam not opened")
        ok, frame = self._cap.read()
        if not ok or frame is None:
            raise RuntimeError("Webcam read failed")
        return StereoFrame.now(left=frame, right=frame.copy())

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def is_stereo(self) -> bool:
        return False
