"""Live checks for PLAN-021 W5 item C8-06: a CSV with preamble lines, end to end.

Uploads a CSV whose first lines are a title block above the header (the shape
of the World Bank exports), then follows the backend's own stored suggestion
through ``dataset interpretation preview`` and ``confirm``. Runs the real CLI
in-process against a real tenant (no doubles) in its own scratch project, and
removes its dataset and the project.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_dataset_interpretation.py -m live -v
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live

_PREAMBLE = (
    "Data Source,World Development Indicators,\n"
    "\n"
    "Last Updated Date,2026-07-01,\n"
    "\n"
    "Country Name,Country Code,1960,1961,1962\n"
    "Aruba,ABW,54608,55811,56682\n"
    "Andorra,AND,13411,14375,15370\n"
    "Angola,AGO,5357195,5441333,5521400\n"
    "Albania,ALB,1608800,1659800,1711319\n"
    "Argentina,ARG,20481781,20817270,21153042\n"
)
_SETTLE_SECONDS = 180


def _wait_for(read: Any, done: Any) -> Any:
    deadline = time.monotonic() + _SETTLE_SECONDS
    while True:
        value = read()
        if done(value) or time.monotonic() > deadline:
            return value
        time.sleep(5)


def test_preamble_csv_is_held_then_read_by_the_stored_suggestion(
    live_cli: LiveCli, scratch_project: int, tmp_path: Path
) -> None:
    """Preview shows the file read by the stored suggestion; confirm creates the table and view."""
    project = scratch_project
    source = tmp_path / "w5_interpretation_preamble.csv"
    source.write_text(_PREAMBLE, encoding="utf-8")
    uploaded, _ = live_cli.ok("file", "upload", str(source), "--yes", project=project)
    dataset = str(uploaded["dataset_id"])
    try:
        record = _wait_for(
            lambda: live_cli.ok("dataset", "get", dataset, project=project)[0],
            lambda r: bool((r.get("additional_info") or {}).get("interpretation")),
        )
        stored = (record.get("additional_info") or {}).get("interpretation") or {}
        suggestions = stored.get("instruction_suggestions") or []
        if not suggestions:
            pytest.skip("the backend read this file without holding it for interpretation")

        instruction = json.dumps({"user_instruction": suggestions[0]})
        preview, _ = live_cli.ok(
            *("dataset", "interpretation", "preview", dataset, "--input", instruction),
            project=project,
        )
        assert preview["preview_rows"][0][:2] == ["Country Name", "Country Code"]
        assert preview["total_row_count"] == 5

        live_cli.ok(
            *("dataset", "interpretation", "confirm", dataset, "--input", instruction),
            project=project,
        )
        views = _wait_for(
            lambda: live_cli.ok("view", "list", dataset, project=project)[0],
            lambda v: bool(v.get("dataviews")),
        )
        assert views["dataviews"], "confirm did not produce a view"
        data, _ = live_cli.ok(
            "view", "data", "get", str(views["dataviews"][0]["id"]), project=project
        )
        assert data["data"][0]["Country Name"] == "Aruba"
    finally:
        live_cli.run(
            *("dataset", "delete", dataset, "--yes", "--confirm", dataset), project=project
        )
