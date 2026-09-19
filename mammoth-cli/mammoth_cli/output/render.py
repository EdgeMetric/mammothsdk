"""Render normalized results for each output mode.

Machine modes (json, ndjson) write pure data to stdout. Human modes (table,
plain) never leak into machine stdout. Diagnostics always go to stderr.

NDJSON is a versioned lifecycle stream (version 2): a ``start`` frame, zero or
more ``item`` frames, then one terminal ``end`` or ``error`` frame.  The
``ndjson_legacy`` render argument retains the former item-only format for
embedded callers that explicitly opt into it.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, TextIO

import yaml

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
        yaml.safe_dump(envelope, stream, sort_keys=True, allow_unicode=True)
    elif output == "plain":
        _render_plain(envelope.get("data"), stream)
    elif output == "table":
        _render_table(envelope.get("data"), stream)
    else:  # pragma: no cover - guarded by option validation
        raise ValueError(f"unknown output mode: {output}")


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


def _render_table(data: Any, stream: TextIO) -> None:
    from rich.console import Console
    from rich.table import Table

    console = Console(file=stream)
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
