from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


class RoundStatus(str, Enum):
    STARTED = "started"
    SCANNED = "scanned"
    DETECTIONS_MADE = "detections_made"
    TARGETS_SELECTED = "targets_selected"
    CANCELLED = "cancelled"
    FAILED = "failed"


# Allowed forward transitions. Any status may also transition to CANCELLED or FAILED.
TRANSITIONS: dict[RoundStatus, set[RoundStatus]] = {
    RoundStatus.STARTED: {RoundStatus.SCANNED, RoundStatus.CANCELLED, RoundStatus.FAILED},
    RoundStatus.SCANNED: {RoundStatus.DETECTIONS_MADE, RoundStatus.CANCELLED, RoundStatus.FAILED},
    RoundStatus.DETECTIONS_MADE: {RoundStatus.TARGETS_SELECTED, RoundStatus.CANCELLED, RoundStatus.FAILED},
    RoundStatus.TARGETS_SELECTED: set(),
    RoundStatus.CANCELLED: set(),
    RoundStatus.FAILED: set(),
}


def can_transition(src: RoundStatus, dst: RoundStatus) -> bool:
    return dst in TRANSITIONS[src]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class DetectionRound:
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_type: str = ""
    confidence_threshold: float = 0.5
    status: RoundStatus = RoundStatus.STARTED
    class_filter_applied: bool = True
    raw_path: str | None = None
    detection_path: str | None = None
    target_path: str | None = None
    started_at: str = field(default_factory=_iso_now)
    scanned_at: str | None = None
    detections_at: str | None = None
    targets_at: str | None = None
    cancelled_at: str | None = None
    failed_at: str | None = None
    detections: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "DetectionRound":
        data = dict(d)
        data["status"] = RoundStatus(data.get("status", RoundStatus.STARTED.value))
        return cls(**data)

    def advance(self, dst: RoundStatus) -> None:
        if not can_transition(self.status, dst):
            raise ValueError(f"Illegal transition {self.status.value} -> {dst.value}")
        self.status = dst
        stamp = _iso_now()
        if dst is RoundStatus.SCANNED:
            self.scanned_at = stamp
        elif dst is RoundStatus.DETECTIONS_MADE:
            self.detections_at = stamp
        elif dst is RoundStatus.TARGETS_SELECTED:
            self.targets_at = stamp
        elif dst is RoundStatus.CANCELLED:
            self.cancelled_at = stamp
        elif dst is RoundStatus.FAILED:
            self.failed_at = stamp
