"""Dataset health, stated wherever a dataset appears in a result.

A dataset's ``status`` can say it did not load cleanly, but a bare status word
reads as fine to an agent that is looking for rows. :func:`with_dataset_health`
turns each such status into a ``dataset_health`` entry that says what it means
and which command fixes it. It runs on every result, read or write, and never
makes a request.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

#: Status to (what it means, which command to run first) -- ``{id}`` is filled in.
_UNHEALTHY: dict[str, tuple[str, str]] = {
    "has_unstructured_data": (
        "Some rows of this file could not be split into columns, so they are held "
        "apart and the dataset may have few or no usable rows. The usual cause is "
        "the wrong delimiter or quote character.",
        "mammoth dataset file-settings get {id}, then mammoth dataset file-settings "
        "update {id} with the right delimiter or quote character",
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
        if value.get("status") in _UNHEALTHY and isinstance(value.get("id"), int):
            yield value
        for child in value.values():
            yield from _unhealthy(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _unhealthy(child, depth + 1)


def _entry(record: dict[str, Any]) -> dict[str, Any]:
    detail, fix = _UNHEALTHY[record["status"]]
    return {
        "dataset_id": record["id"],
        "name": record.get("name"),
        "status": record["status"],
        "detail": detail,
        "fix": fix.format(id=record["id"]),
    }
