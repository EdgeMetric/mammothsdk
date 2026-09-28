"""How new data reaches a dataset, stated wherever a file dataset appears.

A dataset made from an uploaded file reads as a one-time snapshot, so an agent
asked for a recurring report concludes nothing new will ever arrive. The next
file appends to the same dataset as a new batch and the dataset's views re-run
on it. :func:`with_new_data_path` adds that path; it never makes a request.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

_HOW = (
    "Made from an uploaded file; the next period's file joins this dataset as a "
    "new batch with mammoth file upload FILE --input '{{\"append_to_ds_id\": {id}}}'. "
    "Its views re-run on the added rows, so a scheduled automation on a view "
    "sends the updated data without anyone rebuilding the pipeline."
)
#: Nesting to search: a result, a listing inside it, a record in the listing.
_MAX_DEPTH = 3


def with_new_data_path(data: Any) -> Any:
    """Return ``data`` with a ``new_data`` list when any dataset in it was made
    from an uploaded file; anything else is returned unchanged."""
    if not isinstance(data, dict):
        return data
    paths = [
        {
            "dataset_id": record["id"],
            "name": record.get("name"),
            "how": _HOW.format(id=record["id"]),
        }
        for record in _file_datasets(data, 0)
    ]
    if not paths:
        return data
    return {**data, "new_data": paths}


def _file_datasets(value: Any, depth: int) -> Iterator[dict[str, Any]]:
    if depth > _MAX_DEPTH:
        return
    if isinstance(value, dict):
        if _is_file_dataset(value):
            yield value
        for child in value.values():
            yield from _file_datasets(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _file_datasets(child, depth + 1)


def _is_file_dataset(record: dict[str, Any]) -> bool:
    sources = record.get("sources")
    return (
        isinstance(record.get("id"), int)
        and isinstance(sources, list)
        and any(isinstance(s, dict) and s.get("type") == "file" for s in sources)
    )
