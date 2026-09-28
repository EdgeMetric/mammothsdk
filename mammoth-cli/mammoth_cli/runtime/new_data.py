"""How new data reaches a dataset, stated wherever such a dataset appears.

A dataset made from an uploaded file reads as a one-time snapshot, so an agent
asked for a recurring report concludes nothing new will ever arrive; the next
file appends to it as a new batch and its views re-run. A dataset written by a
view's export reads as a standalone copy, so an agent cannot tell what writes it
or what deleting it takes with it. :func:`with_new_data_path`
states either path; it never makes a request.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

_FROM_FILE = (
    "Made from an uploaded file; the next period's file joins this dataset as a "
    "new batch with mammoth file upload FILE --input '{{\"append_to_ds_id\": {id}}}'. "
    "Its views re-run on the added rows, so a scheduled automation on a view "
    "sends the updated data without anyone rebuilding the pipeline."
)
_FROM_EXPORT = (
    "Written by export {export_id} in view {view_id}'s pipeline, which fills it "
    "again on every run of that view. Deleting this dataset also removes that "
    "export; to keep the dataset but stop the updates, run mammoth view export "
    "delete {view_id} {export_id}."
)
#: Nesting to search: a result, a listing inside it, a record in the listing.
_MAX_DEPTH = 3


def with_new_data_path(data: Any) -> Any:
    """Return ``data`` with a ``new_data`` list when any dataset in it was made
    from an uploaded file or is written by a view's export; anything else is
    returned unchanged."""
    if not isinstance(data, dict):
        return data
    paths = [
        {"dataset_id": record["id"], "name": record.get("name"), "how": how}
        for record, how in _fed_datasets(data, 0)
    ]
    if not paths:
        return data
    return {**data, "new_data": paths}


def with_file_upload_path(data: Any, dataset_id: int) -> Any:
    """Return file settings with a ``new_data`` entry: settings with a delimiter
    exist only for a parsed upload, which the next period's file can join."""
    info = data.get("info") if isinstance(data, dict) else None
    if not isinstance(info, dict) or not info.get("delimiter"):
        return data
    how = _FROM_FILE.format(id=dataset_id)
    return {**data, "new_data": [{"dataset_id": dataset_id, "name": None, "how": how}]}


def _fed_datasets(value: Any, depth: int) -> Iterator[tuple[dict[str, Any], str]]:
    if depth > _MAX_DEPTH:
        return
    if isinstance(value, dict):
        how = _how(value)
        if how is not None:
            yield value, how
        for child in value.values():
            yield from _fed_datasets(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _fed_datasets(child, depth + 1)


def _how(record: dict[str, Any]) -> str | None:
    if not isinstance(record.get("id"), int):
        return None
    info = record.get("additional_info")
    if (
        isinstance(info, dict)
        and isinstance(info.get("DATAVIEW_ID"), int)
        and isinstance(info.get("TRIGGER_ID"), int)
    ):
        return _FROM_EXPORT.format(view_id=info["DATAVIEW_ID"], export_id=info["TRIGGER_ID"])
    sources = record.get("sources")
    if isinstance(sources, list) and any(
        isinstance(s, dict) and s.get("type") == "file" for s in sources
    ):
        return _FROM_FILE.format(id=record["id"])
    return None
