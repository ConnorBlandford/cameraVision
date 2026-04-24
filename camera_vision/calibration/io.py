from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ndarray_to_list(x: Any) -> Any:
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, dict):
        return {k: _ndarray_to_list(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_ndarray_to_list(v) for v in x]
    return x


def _list_to_ndarray(d: dict, keys: list[str]) -> None:
    for k in keys:
        if k in d and d[k] is not None:
            d[k] = np.asarray(d[k], dtype=np.float64)


def save_intrinsics(
    path: Path,
    *,
    user: str,
    camera: str,
    image_size: tuple[int, int],
    K: np.ndarray,
    dist: np.ndarray,
    rms: float,
    n_captures: int,
) -> None:
    payload = {
        "type": "intrinsics",
        "metadata": {
            "captured_at": _iso_now(),
            "user": user,
            "camera": camera,
            "n_captures": int(n_captures),
            "rms_reprojection_error": float(rms),
            "image_size": [int(image_size[0]), int(image_size[1])],
        },
        "K": _ndarray_to_list(K),
        "dist": _ndarray_to_list(dist),
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)


def load_intrinsics(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _list_to_ndarray(data, ["K", "dist"])
    return data


def save_extrinsics(
    path: Path,
    *,
    user: str,
    image_size: tuple[int, int],
    R: np.ndarray,
    T: np.ndarray,
    E: np.ndarray,
    F: np.ndarray,
    Q: np.ndarray,
    rms: float,
) -> None:
    payload = {
        "type": "extrinsics",
        "metadata": {
            "captured_at": _iso_now(),
            "user": user,
            "rms_reprojection_error": float(rms),
            "image_size": [int(image_size[0]), int(image_size[1])],
        },
        "R": _ndarray_to_list(R),
        "T": _ndarray_to_list(T),
        "E": _ndarray_to_list(E),
        "F": _ndarray_to_list(F),
        "Q": _ndarray_to_list(Q),
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)


def load_extrinsics(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _list_to_ndarray(data, ["R", "T", "E", "F", "Q"])
    return data
