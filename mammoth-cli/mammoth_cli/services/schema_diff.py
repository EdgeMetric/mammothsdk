"""Compare two datasets' columns and propose the mapping a batch append takes.

``dataset schema-diff DESTINATION SOURCE`` answers "can SOURCE be appended to
DESTINATION, and with which mapping?" before ``batch create``, which refuses an
incomplete mapping. Columns with the same name map to each other. A column that
exists on one side only is a rename when an unmatched column on the other side
has the same type and shares a sample value with it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

#: Sample values kept per column when matching a rename.
SAMPLE_ROWS = 50


def column_samples(rows: Any, columns: Sequence[Mapping[str, Any]]) -> dict[str, set[str]]:
    """``{c_name: distinct non-blank values}`` from a dataset data read.

    The read is ``{"data": {row_number: [cell, ...]}, "headers": [name, ...]}``:
    each row is a list in ``headers`` order (``columns`` order when absent). A
    column no row carries has no entry, so it never matches a rename on values.
    """
    page = rows.get("data") if isinstance(rows, Mapping) else None
    records = [row for row in (page or {}).values() if isinstance(row, Sequence)][:SAMPLE_ROWS]
    headers = rows.get("headers") if isinstance(rows, Mapping) else None
    names = list(headers) if headers else [column["c_name"] for column in columns]
    samples: dict[str, set[str]] = {}
    for column in columns:
        position = next(
            (
                names.index(key)
                for key in (column.get("c_name"), column.get("c_id"))
                if key in names
            ),
            None,
        )
        if position is None:
            continue
        values = {
            str(row[position]).strip()
            for row in records
            if position < len(row) and row[position] is not None
        }
        values.discard("")
        if values:
            samples[column["c_name"]] = values
    return samples


def _type(column: Mapping[str, Any]) -> str:
    return str(column.get("c_type") or "").upper()


def _brief(column: Mapping[str, Any]) -> dict[str, str]:
    return {"c_name": column["c_name"], "c_type": _type(column)}


def schema_diff(
    destination: Sequence[Mapping[str, Any]],
    source: Sequence[Mapping[str, Any]],
    destination_samples: Mapping[str, set[str]],
    source_samples: Mapping[str, set[str]],
) -> dict[str, Any]:
    """Added, removed and renamed columns plus the proposed ``mapping``.

    ``added`` are source columns the destination lacks, ``removed`` are
    destination columns the source lacks; a rename is in neither. ``mapping``
    is ``[{source_c_name, destination_c_name}]``, the shape ``batch create``
    takes, and covers only source columns that have a destination.
    """
    dest_names = {c["c_name"] for c in destination}
    mapping = [
        {"source_c_name": c["c_name"], "destination_c_name": c["c_name"]}
        for c in source
        if c["c_name"] in dest_names
    ]
    dest_open = [c for c in destination if c["c_name"] not in {c["c_name"] for c in source}]
    source_open = [c for c in source if c["c_name"] not in dest_names]
    renamed: list[dict[str, Any]] = []
    for column in list(source_open):
        match = _rename_of(column, dest_open, destination_samples, source_samples)
        if match is None:
            continue
        shared = sorted(source_samples[column["c_name"]] & destination_samples[match["c_name"]])
        renamed.append(
            {
                "source": column["c_name"],
                "destination": match["c_name"],
                "c_type": _type(column),
                "shared_values": shared[:5],
            }
        )
        mapping.append({"source_c_name": column["c_name"], "destination_c_name": match["c_name"]})
        source_open.remove(column)
        dest_open.remove(match)
    return {
        "added": [_brief(c) for c in source_open],
        "removed": [_brief(c) for c in dest_open],
        "renamed": renamed,
        "mapping": mapping,
    }


def _rename_of(
    column: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    destination_samples: Mapping[str, set[str]],
    source_samples: Mapping[str, set[str]],
) -> Mapping[str, Any] | None:
    mine = source_samples.get(column["c_name"], set())
    for other in candidates:
        if _type(other) == _type(column) and mine & destination_samples.get(other["c_name"], set()):
            return other
    return None
