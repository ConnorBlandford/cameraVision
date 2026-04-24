from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from camera_vision.calibration.io import load_extrinsics, load_intrinsics


@dataclass
class CalibrationFile:
    path: Path
    exists: bool
    captured_at: str | None = None
    user: str | None = None
    rms: float | None = None


@dataclass
class CalibrationState:
    intrinsics_left: CalibrationFile
    intrinsics_right: CalibrationFile
    extrinsics: CalibrationFile

    @property
    def intrinsics_ready(self) -> bool:
        return self.intrinsics_left.exists and self.intrinsics_right.exists

    @property
    def fully_calibrated(self) -> bool:
        return self.intrinsics_ready and self.extrinsics.exists


def _read(path: Path, loader) -> CalibrationFile:
    if not path.exists():
        return CalibrationFile(path=path, exists=False)
    try:
        data = loader(path)
        meta = data.get("metadata", {})
        return CalibrationFile(
            path=path,
            exists=True,
            captured_at=meta.get("captured_at"),
            user=meta.get("user"),
            rms=meta.get("rms_reprojection_error"),
        )
    except Exception:
        return CalibrationFile(path=path, exists=True)


def inspect_state(calibrations_dir: Path) -> CalibrationState:
    return CalibrationState(
        intrinsics_left=_read(calibrations_dir / "intrinsics-left.yaml", load_intrinsics),
        intrinsics_right=_read(calibrations_dir / "intrinsics-right.yaml", load_intrinsics),
        extrinsics=_read(calibrations_dir / "extrinsics.yaml", load_extrinsics),
    )
