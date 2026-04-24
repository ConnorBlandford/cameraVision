from __future__ import annotations

import numpy as np

from camera_vision.calibration import (
    load_extrinsics,
    load_intrinsics,
    save_extrinsics,
    save_intrinsics,
)
from camera_vision.calibration.state import inspect_state


def test_intrinsics_yaml_roundtrip(tmp_path):
    K = np.array([[800.0, 0, 320.0], [0, 800.0, 240.0], [0, 0, 1.0]])
    dist = np.array([0.1, -0.2, 0.0, 0.0, 0.0])
    path = tmp_path / "intrinsics-left.yaml"

    save_intrinsics(
        path,
        user="tester",
        camera="left",
        image_size=(640, 480),
        K=K,
        dist=dist,
        rms=0.42,
        n_captures=15,
    )

    data = load_intrinsics(path)
    assert data["type"] == "intrinsics"
    assert data["metadata"]["user"] == "tester"
    assert data["metadata"]["n_captures"] == 15
    assert data["metadata"]["image_size"] == [640, 480]
    np.testing.assert_allclose(data["K"], K)
    np.testing.assert_allclose(data["dist"], dist)


def test_extrinsics_yaml_roundtrip(tmp_path):
    R = np.eye(3)
    T = np.array([[0.06], [0.0], [0.0]])
    E = np.eye(3)
    F = np.eye(3)
    Q = np.eye(4)

    path = tmp_path / "extrinsics.yaml"
    save_extrinsics(
        path,
        user="tester",
        image_size=(1280, 720),
        R=R, T=T, E=E, F=F, Q=Q,
        rms=0.9,
    )

    data = load_extrinsics(path)
    assert data["type"] == "extrinsics"
    assert data["metadata"]["user"] == "tester"
    np.testing.assert_allclose(data["R"], R)
    np.testing.assert_allclose(data["T"], T)
    np.testing.assert_allclose(data["Q"], Q)


def test_inspect_state_reflects_presence(tmp_path):
    state = inspect_state(tmp_path)
    assert not state.intrinsics_left.exists
    assert not state.intrinsics_ready
    assert not state.fully_calibrated

    save_intrinsics(
        tmp_path / "intrinsics-left.yaml",
        user="t", camera="left", image_size=(2, 2),
        K=np.eye(3), dist=np.zeros(5), rms=0.1, n_captures=5,
    )
    save_intrinsics(
        tmp_path / "intrinsics-right.yaml",
        user="t", camera="right", image_size=(2, 2),
        K=np.eye(3), dist=np.zeros(5), rms=0.1, n_captures=5,
    )

    state = inspect_state(tmp_path)
    assert state.intrinsics_ready
    assert not state.fully_calibrated
    assert state.intrinsics_left.user == "t"
