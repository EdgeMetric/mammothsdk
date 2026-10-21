"""Render normalized results for each output mode.

Machine modes (json, ndjson) write pure data to stdout. Human modes (table,
plain) never leak into machine stdout. Diagnostics always go to stderr.

NDJSON is a versioned lifecycle stream (version 2): a ``start`` frame, zero or
more ``item`` frames, then one terminal ``end`` or ``error`` frame.  The
``ndjson_legacy`` render argument retains the former item-only format for
embedded callers that explicitly opt into it.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from typing import Any, TextIO

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENTS, EXIT_USAGE, CliError

from .normalize import normalize

NDJSON_STREAM_VERSION = 2


def render(
    envelope: dict[str, Any],
    *,
    output: str = "json",
    stream: TextIO | None = None,
    ndjson_legacy: bool = False,
) -> None:
    stream = stream if stream is not None else sys.stdout
    # Render is also a public seam used by command tests and integrations;
    # normalize here as a final guard so direct callers cannot emit NaN,
    # dataclass reprs, or secret-bearing SDK objects into machine output.
    envelope = normalize(envelope)
    if output == "json":
        # Pretty for a person at a terminal; compact (one line) when piped,
        # which is what an agent or script reads: same document, roughly half
        # the bytes and tokens. ``MAMMOTH_JSON_PRETTY=1`` forces indentation.
        pretty = _json_pretty(stream)
        json.dump(
            envelope,
            stream,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        stream.write("\n")
    elif output == "ndjson":
        _render_ndjson(envelope, stream, legacy=ndjson_legacy)
    elif output == "yaml":
        # Dump the JSON form of the envelope. ``safe_dump`` refuses dict and list subclasses (data
        # rows, schema documents, revealed secrets) that JSON accepts, so a round trip makes
        # yaml carry exactly what ``--output json`` carries.
        document = json.loads(json.dumps(envelope, ensure_ascii=False, allow_nan=False))
        import yaml  # imported here: only ``--output yaml`` needs it (about 12 ms)

        yaml.safe_dump(document, stream, sort_keys=True, allow_unicode=True)
    elif output in ("plain", "table") and (text := _document_text(envelope)) is not None:
        stream.write(text if text.endswith("\n") else text + "\n")
    elif output == "plain":
        _render_plain(envelope.get("data"), stream)
    elif output == "csv":
        _render_csv(envelope.get("data"), stream)
    elif output == "table":
        _render_table(envelope.get("data"), stream)
    else:  # pragma: no cover - guarded by option validation
        raise ValueError(f"unknown output mode: {output}")


#: Commands whose result is one document to read: human output prints the
#: document itself (the named ``data`` key), not an escaped string in a table.
_DOCUMENT_COMMANDS: dict[str, str] = {"skill show": "text"}


def _document_text(envelope: dict[str, Any]) -> str | None:
    meta = envelope.get("meta")
    data = envelope.get("data")
    if not isinstance(meta, dict) or not isinstance(data, dict):
        return None
    key = _DOCUMENT_COMMANDS.get(str(meta.get("command") or ""))
    value = data.get(key) if key else None
    return value if isinstance(value, str) else None


def _json_pretty(stream: TextIO) -> bool:
    forced = os.environ.get("MAMMOTH_JSON_PRETTY")
    if forced is not None:
        return forced.strip().lower() in {"1", "true", "yes", "on"}
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def _write_ndjson(frame: dict[str, Any], stream: TextIO) -> None:
    """Write exactly one parseable lifecycle frame."""
    stream.write(json.dumps(frame, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")


def _render_ndjson(envelope: dict[str, Any], stream: TextIO, *, legacy: bool = False) -> None:
    """Render a versioned lifecycle stream, or the explicit legacy item stream."""
    data = envelope.get("data")
    if legacy:
        if isinstance(data, list):
            for item in data:
                stream.write(
                    json.dumps(item, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
                )
        else:
            stream.write(
                json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
            )
        return

    schema_version = envelope.get("schema_version")
    meta = envelope.get("meta")
    if "error" in envelope:
        _write_ndjson(
            {
                "schema_version": schema_version,
                "stream_version": NDJSON_STREAM_VERSION,
                "event": "error",
                "complete": False,
                "error": envelope["error"],
                "meta": meta,
            },
            stream,
        )
        return

    _write_ndjson(
        {
            "schema_version": schema_version,
            "stream_version": NDJSON_STREAM_VERSION,
            "event": "start",
            "meta": meta,
        },
        stream,
    )
    items = data if isinstance(data, list) else [data]
    for index, item in enumerate(items):
        _write_ndjson(
            {
                "schema_version": schema_version,
                "stream_version": NDJSON_STREAM_VERSION,
                "event": "item",
                "index": index,
                "data": item,
            },
            stream,
        )
    _write_ndjson(
        {
            "schema_version": schema_version,
            "stream_version": NDJSON_STREAM_VERSION,
            "event": "end",
            "complete": True,
            "count": len(items),
            "meta": meta,
        },
        stream,
    )


def _render_plain(data: Any, stream: TextIO) -> None:
    if isinstance(data, list):
        for item in data:
            stream.write(f"{_scalar(item)}\n")
    elif isinstance(data, dict):
        for key in data:
            stream.write(f"{key}\t{_scalar(data[key])}\n")
    else:
        stream.write(f"{_scalar(data)}\n")


#: Keys a listing result keeps its records under, tried in this order.
_LISTING_KEYS = (
    "data",
    "datasets",
    "dataviews",
    "files",
    "folders",
    "projects",
    "views",
    "items",
    "results",
)


def _record_list(value: Any) -> list[dict[str, Any]] | None:
    if isinstance(value, list) and value and all(isinstance(row, dict) for row in value):
        return value
    return None


def _csv_rows(data: Any) -> list[dict[str, Any]] | None:
    """The result's rows: ``data`` itself, or the one list of records inside a result."""
    if isinstance(data, dict):
        for key in _LISTING_KEYS:
            rows = _record_list(data.get(key))
            if rows is not None:
                return rows
        # Otherwise the single list of records, ignoring health and warning side lists.
        candidates = [
            rows
            for key, value in data.items()
            if not str(key).endswith(("_health", "warnings", "problems"))
            and (rows := _record_list(value)) is not None
        ]
        return candidates[0] if len(candidates) == 1 else None
    return _record_list(data)


def _render_csv(data: Any, stream: TextIO) -> None:
    rows = _csv_rows(data)
    if rows is None:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="This result has no rows to write as CSV.",
            exit_status=EXIT_USAGE,
            hint="Use -o json, or a command that returns rows (view data explore, view data get).",
        )
    columns = list(dict.fromkeys(str(key) for row in rows for key in row))
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_scalar(row.get(column)) for column in columns])


def _render_table(data: Any, stream: TextIO) -> None:
    from rich.console import Console
    from rich.table import Table

    console = Console(file=stream)
    if isinstance(data, dict) and list(data) == ["result"] and isinstance(data["result"], list):
        data = data["result"]  # a list result wrapped as {"result": [...]}: one row per item
    if isinstance(data, list) and any(isinstance(row, dict) for row in data):
        columns: list[str] = []
        for row in data:
            if isinstance(row, dict):
                for key in row:
                    key_text = str(key)
                    if key_text not in columns:
                        columns.append(key_text)
        if any(not isinstance(row, dict) for row in data):
            columns.append("value")
        table = Table(*[str(c) for c in columns])
        for row in data:
            if isinstance(row, dict):
                table.add_row(*[_scalar(row.get(c)) for c in columns])
            else:
                table.add_row(*[_scalar(row) if column == "value" else "" for column in columns])
        console.print(table)
    elif isinstance(data, dict):
        table = Table("field", "value")
        for key in data:
            table.add_row(str(key), _scalar(data[key]))
        console.print(table)
    else:
        console.print(_scalar(data))


def _scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
