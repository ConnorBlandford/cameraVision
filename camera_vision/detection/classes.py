"""COCO vocabulary and target-type resolution.

`target_type` comes from the UI as free text ("Apples", "Corks", or whatever
the user types). We map it to a COCO class name where possible; unknown types
fall through and the round is flagged `class_filter_applied=False`.

Class IDs follow RF-DETR's sparse 91-class mapping (ids 1..90 with gaps for
omitted categories like "hat"/"shoe"). We source the mapping from `rfdetr`
directly so detector output and resolver share one source of truth.
"""
from __future__ import annotations

from rfdetr.assets.coco_classes import COCO_CLASSES as _RFDETR_COCO

# id -> name (sparse, 80 entries, ids 1..90 with gaps)
COCO_ID_TO_NAME: dict[int, str] = dict(_RFDETR_COCO)
COCO_NAME_TO_ID: dict[str, int] = {v: k for k, v in COCO_ID_TO_NAME.items()}
COCO_CLASSES: list[str] = list(COCO_ID_TO_NAME.values())

# User-facing target types map to a COCO class name (or None if unsupported).
TARGET_ALIASES: dict[str, str | None] = {
    "apple": "apple",
    "apples": "apple",
    "orange": "orange",
    "oranges": "orange",
    # cork has no COCO analogue — handled via class_filter_applied=False
}


def resolve_target_class(target_type: str) -> str | None:
    """Return the COCO class name for a target_type, or None if unsupported.

    Match is case-insensitive and tolerant of trailing whitespace.
    """
    key = target_type.strip().lower()
    if not key:
        return None
    if key in TARGET_ALIASES:
        return TARGET_ALIASES[key]
    if key in COCO_NAME_TO_ID:
        return key
    # Try pluralised forms generically
    if key.endswith("s") and key[:-1] in COCO_NAME_TO_ID:
        return key[:-1]
    return None


def lookup_class_name(class_id: int) -> str:
    """Resolve a raw detector class id to its COCO name, or a fallback placeholder."""
    return COCO_ID_TO_NAME.get(int(class_id), f"class_{int(class_id)}")
