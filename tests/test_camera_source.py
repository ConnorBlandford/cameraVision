"""Camera source contract: read() returns (left, right, timestamp) and both
arrays are identical for the webcam stand-in."""
from __future__ import annotations

import numpy as np
import pytest

from camera_vision.sources.base import CameraSource, StereoFrame


class FakeWebcam(CameraSource):
    """In-memory CameraSource matching the webcam contract — same frame on both sides."""

    def __init__(self, frame: np.ndarray) -> None:
        self._frame = frame
        self._opened = False

    def open(self) -> None: self._opened = True
    def close(self) -> None: self._opened = False

    def read(self) -> StereoFrame:
        assert self._opened
        return StereoFrame.now(left=self._frame, right=self._frame.copy())

    @property
    def is_stereo(self) -> bool: return False


def test_webcam_returns_identical_left_right():
    img = (np.random.rand(32, 48, 3) * 255).astype(np.uint8)
    with FakeWebcam(img) as src:
        f = src.read()
        assert f.left.shape == img.shape
        assert f.right.shape == img.shape
        np.testing.assert_array_equal(f.left, f.right)
        # separate buffers — mutating one does not affect the other
        f.right[0, 0] = [0, 0, 0]
        assert not np.array_equal(f.left, f.right)


def test_context_manager_opens_and_closes():
    src = FakeWebcam(np.zeros((4, 4, 3), dtype=np.uint8))
    with src:
        assert src._opened is True
    assert src._opened is False


def test_read_before_open_raises():
    src = FakeWebcam(np.zeros((4, 4, 3), dtype=np.uint8))
    with pytest.raises(AssertionError):
        src.read()
