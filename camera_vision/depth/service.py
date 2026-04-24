from __future__ import annotations

import numpy as np


class DepthService:
    """Placeholder for stereo depth estimation. Requires extrinsics."""

    def __init__(self, extrinsics: dict | None = None) -> None:
        self._extrinsics = extrinsics

    @property
    def ready(self) -> bool:
        return self._extrinsics is not None

    def compute(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Depth scanning is not implemented yet")
