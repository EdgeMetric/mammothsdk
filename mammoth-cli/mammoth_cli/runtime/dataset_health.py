"""Dataset health, stated wherever a dataset appears in a result.

A dataset's ``status`` can say it did not load cleanly, but a bare status word
reads as fine to an agent that is looking for rows. :func:`with_dataset_health`
turns each such status into a ``dataset_health`` entry that says what it means
and which command fixes it. It runs on every result, read or write, and never
makes a request.
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Iterator
from typing import Any

#: Status to what it means. The cause is not named: the backend holds a file
#: for more than one reason (an ambiguous header, a preamble, a quote
#: character), and it stores its own suggestion; :func:`_entry` quotes that.
_UNHEALTHY: dict[str, str] = {
    "has_unstructured_data": (
        "This file was not loaded as a finished table: it has more than one plausible "
        "way to be read, so the dataset may have few or no usable rows."
    ),
    "need_action": "This dataset needs a user decision before it is usable.",
}
#: Nesting to search: a result, a listing inside it, a record in the listing.
_MAX_DEPTH = 3


#: Keys under which a result carries dataset records; every record there gets a health entry.
_DATASET_KEYS = frozenset({"datasets", "dataset"})
_HEALTHY_STATUS = "ready"


def with_dataset_health(data: Any) -> Any:
    """Return ``data`` with a ``dataset_health`` list.

    Every dataset under ``datasets``/``dataset`` gets an entry (``health`` is
    ``healthy``, ``unhealthy`` or ``unknown``), so a clean listing says it was
    looked at. A record elsewhere gets one only when its status is unhealthy.
    Anything without dataset records is returned unchanged.
    """
    if not isinstance(data, dict):
        return data
    health = [_entry(record) for record in _dataset_records(data, 0, False)]
    if not health:
        return data
    return {**data, "dataset_health": health}


def _dataset_records(value: Any, depth: int, listed: bool) -> Iterator[dict[str, Any]]:
    if depth > _MAX_DEPTH:
        return
    if isinstance(value, dict):
        if _dataset_id(value) is not None and (listed or value.get("status") in _UNHEALTHY):
            yield value
        for key, child in value.items():
            yield from _dataset_records(child, depth + 1, key in _DATASET_KEYS)
    elif isinstance(value, list):
        for child in value:
            yield from _dataset_records(child, depth + 1, listed)


def _dataset_id(record: dict[str, Any]) -> int | None:
    """A dataset record names itself ``id``; a job's response names it ``ds_id``."""
    for key in ("id", "ds_id"):
        if isinstance(record.get(key), int):
            return int(record[key])
    return None


def _stored_interpretation(record: dict[str, Any]) -> dict[str, Any]:
    info = record.get("additional_info")
    stored = info.get("interpretation") if isinstance(info, dict) else None
    return stored if isinstance(stored, dict) else {}


def _stored_strings(stored: dict[str, Any], key: str) -> list[str]:
    values = stored.get(key)
    return [v for v in values if isinstance(v, str) and v] if isinstance(values, list) else []


def _status_info_text(record: dict[str, Any]) -> str:
    """The record's own ``status_info`` text, quoted as the backend wrote it."""
    info = record.get("status_info")
    if not isinstance(info, dict):
        return ""
    return " ".join(v.strip() for v in info.values() if isinstance(v, str) and v.strip())


def _entry(record: dict[str, Any]) -> dict[str, Any]:
    status = record.get("status")
    if status not in _UNHEALTHY:
        return _clean_entry(record, status)
    dataset_id = _dataset_id(record)
    stored = _stored_interpretation(record)
    reasons = _stored_strings(stored, "reasons")
    suggestions = _stored_strings(stored, "instruction_suggestions")
    detail = _UNHEALTHY[record["status"]]
    if reasons:
        detail += " The backend recorded: " + "; ".join(reasons) + "."
    said = _status_info_text(record)
    if said:
        detail += f" Status info: {said}"
    entry: dict[str, Any] = {
        "dataset_id": dataset_id,
        "name": record.get("name"),
        "status": record["status"],
        "health": "unhealthy",
        "detail": detail,
    }
    if suggestions:
        entry["stored_suggestions"] = suggestions
        entry["fix"] = (
            f"mammoth dataset interpretation preview {dataset_id} --input "
            + shlex.quote(json.dumps({"user_instruction": suggestions[0]}))
            + "; then mammoth dataset interpretation confirm "
            + f"{dataset_id} with the same input"
        )
    else:
        entry["fix"] = (
            f"mammoth dataset get {dataset_id} shows the suggestions the backend stored "
            f"(additional_info.interpretation); mammoth dataset broken-rows list {dataset_id} "
            "shows the rows that did not fit"
        )
    return entry


def _clean_entry(record: dict[str, Any], status: Any) -> dict[str, Any]:
    """A healthy dataset, or one whose status this CLI does not classify."""
    healthy = status == _HEALTHY_STATUS
    return {
        "dataset_id": _dataset_id(record),
        "name": record.get("name"),
        "status": status,
        "health": "healthy" if healthy else "unknown",
        "detail": (
            "Loaded and readable."
            if healthy
            else f"Status {status!r} is not one this CLI classifies; read the dataset "
            "before relying on its rows."
        ),
    }
