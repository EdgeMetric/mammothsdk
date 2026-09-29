"""Dataset health, stated wherever a dataset appears in a result.

A dataset's ``status`` can say it did not load cleanly, but a bare status word
reads as fine to an agent that is looking for rows. :func:`with_dataset_health`
turns each such status into a ``dataset_health`` entry that says what it means
and which command fixes it. It runs on every result, read or write, and never
makes a request.
"""

from __future__ import annotations

import json
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
}
#: Nesting to search: a result, a listing inside it, a record in the listing.
_MAX_DEPTH = 3


def with_dataset_health(data: Any) -> Any:
    """Return ``data`` with a ``dataset_health`` list when any dataset in it is
    unhealthy; anything else is returned unchanged."""
    if not isinstance(data, dict):
        return data
    health = [_entry(record) for record in _unhealthy(data, 0)]
    if not health:
        return data
    return {**data, "dataset_health": health}


def _unhealthy(value: Any, depth: int) -> Iterator[dict[str, Any]]:
    if depth > _MAX_DEPTH:
        return
    if isinstance(value, dict):
        if value.get("status") in _UNHEALTHY and _dataset_id(value) is not None:
            yield value
        for child in value.values():
            yield from _unhealthy(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _unhealthy(child, depth + 1)


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


def _entry(record: dict[str, Any]) -> dict[str, Any]:
    dataset_id = _dataset_id(record)
    stored = _stored_interpretation(record)
    reasons = _stored_strings(stored, "reasons")
    suggestions = _stored_strings(stored, "instruction_suggestions")
    detail = _UNHEALTHY[record["status"]]
    if reasons:
        detail += " The backend recorded: " + "; ".join(reasons) + "."
    entry: dict[str, Any] = {
        "dataset_id": dataset_id,
        "name": record.get("name"),
        "status": record["status"],
        "detail": detail,
    }
    if suggestions:
        entry["stored_suggestions"] = suggestions
        entry["fix"] = (
            f"mammoth dataset interpretation preview {dataset_id} --input "
            + json.dumps({"user_instruction": suggestions[0]})
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
