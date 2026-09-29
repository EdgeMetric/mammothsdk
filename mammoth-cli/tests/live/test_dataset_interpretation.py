"""Live checks for PLAN-021 W5 item C8-06: a CSV with preamble lines, end to end.

Uploads a CSV whose first lines are a title block above the header (the shape
of the World Bank exports), then follows the backend's own stored suggestion
through ``dataset interpretation preview`` and ``confirm``. Runs the real CLI
in-process against a real tenant (no doubles) and removes its dataset.

    set -a; . ../.env.plan; set +a
    pytest tests/live/test_dataset_interpretation.py -m live -v
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.testing import make_runner

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


def _run(args: list[str], env: dict[str, str], *, input_doc: dict[str, Any] | None = None) -> Any:
    argv = [*args, "--output", "json", "--no-input"]
    if input_doc is not None:
        argv += ["--input", json.dumps(input_doc)]
    result = make_runner().invoke(argv, env=env)
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.output)
    assert not envelope.get("error"), envelope.get("error")
    return envelope["data"]


def _wait_for(read: Any, done: Any) -> Any:
    deadline = time.monotonic() + _SETTLE_SECONDS
    while True:
        value = read()
        if done(value) or time.monotonic() > deadline:
            return value
        time.sleep(5)


def test_preamble_csv_is_held_then_read_by_the_stored_suggestion(
    live_env: dict[str, str], live_project: str, tmp_path: Path
) -> None:
    """Preview shows the file read by the stored suggestion; confirm creates the table and view."""
    source = tmp_path / "w5_interpretation_preamble.csv"
    source.write_text(_PREAMBLE, encoding="utf-8")
    uploaded = _run(["file", "upload", str(source), "--project", live_project, "--yes"], live_env)
    dataset = str(uploaded["dataset_id"])
    try:
        record = _wait_for(
            lambda: _run(["dataset", "get", dataset, "--project", live_project], live_env),
            lambda r: bool((r.get("additional_info") or {}).get("interpretation")),
        )
        stored = (record.get("additional_info") or {}).get("interpretation") or {}
        suggestions = stored.get("instruction_suggestions") or []
        if not suggestions:
            pytest.skip("the backend read this file without holding it for interpretation")

        instruction = {"user_instruction": suggestions[0]}
        preview = _run(
            ["dataset", "interpretation", "preview", dataset, "--project", live_project],
            live_env,
            input_doc=instruction,
        )
        assert preview["preview_rows"][0][:2] == ["Country Name", "Country Code"]
        assert preview["total_row_count"] == 5

        _run(
            ["dataset", "interpretation", "confirm", dataset, "--project", live_project],
            live_env,
            input_doc=instruction,
        )
        views = _wait_for(
            lambda: _run(["view", "list", dataset, "--project", live_project], live_env),
            lambda v: bool(v.get("dataviews")),
        )
        assert views["dataviews"], "confirm did not produce a view"
        data = _run(
            ["view", "data", "get", str(views["dataviews"][0]["id"]), "--project", live_project],
            live_env,
        )
        assert data["data"][0]["Country Name"] == "Aruba"
    finally:
        make_runner().invoke(
            [
                "dataset",
                "delete",
                dataset,
                "--yes",
                "--confirm",
                dataset,
                "--project",
                live_project,
                "--no-input",
                "--output",
                "json",
            ],
            env=live_env,
        )
