"""Render normalized results for each output mode.

Machine modes (json, ndjson) write pure data to stdout. Human modes (table,
plain) never leak into machine stdout. Diagnostics always go to stderr.
"""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

import yaml


def render(
    envelope: dict[str, Any],
    *,
    output: str = "json",
    stream: TextIO | None = None,
) -> None:
    stream = stream if stream is not None else sys.stdout
    if output == "json":
        json.dump(envelope, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
    elif output == "ndjson":
        _render_ndjson(envelope, stream)
    elif output == "yaml":
        yaml.safe_dump(envelope, stream, sort_keys=True, allow_unicode=True)
    elif output == "plain":
        _render_plain(envelope.get("data"), stream)
    elif output == "table":
        _render_table(envelope.get("data"), stream)
    else:  # pragma: no cover - guarded by option validation
        raise ValueError(f"unknown output mode: {output}")


def _render_ndjson(envelope: dict[str, Any], stream: TextIO) -> None:
    data = envelope.get("data")
    if isinstance(data, list):
        for item in data:
            stream.write(json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n")
    else:
        stream.write(json.dumps(data, sort_keys=True, ensure_ascii=False) + "\n")


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
    if isinstance(data, list) and data and isinstance(data[0], dict):
        columns = list(data[0].keys())
        table = Table(*[str(c) for c in columns])
        for row in data:
            table.add_row(*[_scalar(row.get(c)) for c in columns])
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
