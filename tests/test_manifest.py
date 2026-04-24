from __future__ import annotations

import pytest

from camera_vision.manifest import DetectionRound, ManifestStore, RoundStatus, can_transition


def test_status_transition_table():
    assert can_transition(RoundStatus.STARTED, RoundStatus.SCANNED)
    assert can_transition(RoundStatus.SCANNED, RoundStatus.DETECTIONS_MADE)
    assert can_transition(RoundStatus.DETECTIONS_MADE, RoundStatus.TARGETS_SELECTED)

    assert not can_transition(RoundStatus.STARTED, RoundStatus.DETECTIONS_MADE)
    assert not can_transition(RoundStatus.TARGETS_SELECTED, RoundStatus.CANCELLED)

    # Cancellation / failure reachable from any live state
    for live in (RoundStatus.STARTED, RoundStatus.SCANNED, RoundStatus.DETECTIONS_MADE):
        assert can_transition(live, RoundStatus.CANCELLED)
        assert can_transition(live, RoundStatus.FAILED)


def test_advance_sets_status_and_timestamp():
    r = DetectionRound(target_type="apples")
    assert r.scanned_at is None
    r.advance(RoundStatus.SCANNED)
    assert r.status is RoundStatus.SCANNED
    assert r.scanned_at is not None


def test_illegal_transition_raises():
    r = DetectionRound(target_type="apples")
    with pytest.raises(ValueError):
        r.advance(RoundStatus.TARGETS_SELECTED)


def test_manifest_append_and_update_roundtrip(tmp_path):
    store = ManifestStore(tmp_path / "manifest.json")
    r = DetectionRound(target_type="apples", confidence_threshold=0.5)
    store.append(r)

    loaded = store.get(r.uuid)
    assert loaded is not None
    assert loaded.target_type == "apples"
    assert loaded.status is RoundStatus.STARTED

    updated = store.advance(r.uuid, RoundStatus.SCANNED, raw_path="data/scan_images/r.jpg")
    assert updated.status is RoundStatus.SCANNED
    assert updated.raw_path == "data/scan_images/r.jpg"

    rounds = store.list_rounds()
    assert len(rounds) == 1
    assert rounds[0].status is RoundStatus.SCANNED


def test_manifest_duplicate_uuid_rejected(tmp_path):
    store = ManifestStore(tmp_path / "manifest.json")
    r = DetectionRound(target_type="apples")
    store.append(r)
    with pytest.raises(ValueError):
        store.append(r)


def test_manifest_survives_process_restart(tmp_path):
    path = tmp_path / "manifest.json"
    s1 = ManifestStore(path)
    r = DetectionRound(target_type="oranges")
    s1.append(r)

    s2 = ManifestStore(path)
    loaded = s2.get(r.uuid)
    assert loaded is not None
    assert loaded.target_type == "oranges"
