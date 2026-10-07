"""Collects one row per fuzz case and renders the markdown report."""

from __future__ import annotations

import os
import tempfile
import threading
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPORT_ENV = "MAMMOTH_FUZZ_REPORT"

_LOCK = threading.Lock()


@dataclass(frozen=True)
class Row:
    command: str
    case: str
    outcome: str
    stderr: str


ROWS: list[Row] = []


def record(row: Row) -> None:
    with _LOCK:
        ROWS.append(row)


def report_path() -> Path:
    return Path(
        os.environ.get(REPORT_ENV) or Path(tempfile.gettempdir()) / "mammoth-cli-fuzz-report.md"
    )


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def write_report() -> Path | None:
    if not ROWS:
        return None
    counts = Counter(row.outcome.split(":")[0].split(" ")[0] for row in ROWS)
    lines = [
        "# mammoth-cli input fuzz report",
        "",
        f"{len(ROWS)} cases: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())),
        "",
        "| command | case | outcome | first line of stderr |",
        "|---|---|---|---|",
    ]
    for row in sorted(ROWS, key=lambda r: (r.outcome.startswith("PASS"), r.command, r.case)):
        lines.append(
            f"| {_cell(row.command)} | {_cell(row.case)} | "
            f"{_cell(row.outcome)} | {_cell(row.stderr)} |"
        )
    path = report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
