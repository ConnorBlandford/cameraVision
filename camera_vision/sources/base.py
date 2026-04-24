from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np


@dataclass(frozen=True)
class StereoFrame:
    left: np.ndarray
    right: np.ndarray
    timestamp: datetime

    @staticmethod
    def now(left: np.ndarray, right: np.ndarray) -> "StereoFrame":
        return StereoFrame(left=left, right=right, timestamp=datetime.now(timezone.utc))


class CameraSource(ABC):
    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def read(self) -> StereoFrame: ...

    @abstractmethod
    def close(self) -> None: ...

    @property
    @abstractmethod
    def is_stereo(self) -> bool:
        """True when left and right come from physically distinct cameras."""

    def __enter__(self) -> "CameraSource":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
