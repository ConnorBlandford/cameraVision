from __future__ import annotations

import json
import threading
from pathlib import Path

from camera_vision.manifest.schema import DetectionRound, RoundStatus


class ManifestStore:
    """Single-file JSON manifest of detection rounds. Writes are serialised
    behind a lock and done via atomic replace so the file is never left half-written.
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._write_all([])

    def _write_all(self, rounds: list[dict]) -> None:
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rounds, f, indent=2)
        tmp.replace(self._path)

    def _read_all(self) -> list[dict]:
        if not self._path.exists():
            return []
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_rounds(self) -> list[DetectionRound]:
        with self._lock:
            return [DetectionRound.from_dict(d) for d in self._read_all()]

    def get(self, round_id: str) -> DetectionRound | None:
        with self._lock:
            for d in self._read_all():
                if d.get("uuid") == round_id:
                    return DetectionRound.from_dict(d)
        return None

    def append(self, round_: DetectionRound) -> None:
        with self._lock:
            rounds = self._read_all()
            if any(r.get("uuid") == round_.uuid for r in rounds):
                raise ValueError(f"Round {round_.uuid} already exists")
            rounds.append(round_.to_dict())
            self._write_all(rounds)

    def update(self, round_: DetectionRound) -> None:
        with self._lock:
            rounds = self._read_all()
            for i, r in enumerate(rounds):
                if r.get("uuid") == round_.uuid:
                    rounds[i] = round_.to_dict()
                    self._write_all(rounds)
                    return
        raise KeyError(f"Round {round_.uuid} not found")

    def advance(self, round_id: str, dst: RoundStatus, **fields) -> DetectionRound:
        with self._lock:
            rounds = self._read_all()
            for i, r in enumerate(rounds):
                if r.get("uuid") == round_id:
                    round_ = DetectionRound.from_dict(r)
                    round_.advance(dst)
                    for k, v in fields.items():
                        setattr(round_, k, v)
                    rounds[i] = round_.to_dict()
                    self._write_all(rounds)
                    return round_
        raise KeyError(f"Round {round_id} not found")
