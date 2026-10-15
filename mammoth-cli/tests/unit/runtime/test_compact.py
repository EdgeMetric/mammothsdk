"""Lean success payloads: dashboard writes return ids, key values and verify by default.

``dashboard figure add`` and the other dashboard writes returned the whole
canvas (15-20 KB, mostly nulls) when the agent needs the new ids and a check.
By default the canvas becomes a short summary (pages, figures), the planner's
``plan``/``specs`` are left out, and null-only fields are dropped. ``--full``
returns the old payload.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.compact import COMPACT_COMMANDS, FULL_FLAG, with_compact
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.strict import validate_extra_args


def _null_figure(index: int) -> dict[str, Any]:
    figure: dict[str, Any] = {"id": f"f{index}", "kind": "hbar", "title": f"Chart {index}"}
    figure.update({f"option_{n}": None for n in range(60)})
    figure["style"] = {f"s{n}": None for n in range(20)}
    return figure


def _figure_add_result() -> dict[str, Any]:
    canvas = {
        "pages": [
            {"id": "p1", "title": "Overview", "added": [_null_figure(i) for i in range(6)]},
            {"id": "p2", "title": "Detail", "added": [_null_figure(i) for i in range(6, 12)]},
        ],
        "theme": {f"t{n}": None for n in range(40)},
    }
    return {
        "figure_id": "f11",
        "page_id": "p2",
        "bake_job_id": 99,
        "sequence": 4,
        "layout_key": None,
        "canvas": canvas,
        "plan": {"hints": {"x": list(range(200))}},
        "specs": [{"spec": n} for n in range(50)],
        "warnings": [],
        "figure_check": {"problems": [], "checked": True},
        "verify": {"verified": True, "outcome": "settled", "next_command": None},
    }


def _inv(command_id: str = "dashboard.figure.add", **overrides: Any) -> Invocation:
    return Invocation(command_id=command_id, positionals={"dashboard_id": 7}, **overrides)


def test_figure_add_is_compact_by_default_and_keeps_ids_checks_and_verify() -> None:
    full = _figure_add_result()
    data = with_compact(_inv(), full)
    assert len(json.dumps(full)) > 15_000
    assert len(json.dumps(data)) < 2_000
    for key in ("figure_id", "page_id", "bake_job_id", "sequence", "figure_check"):
        assert data[key] == full[key]
    assert data["verify"] == full["verify"]  # verify is never trimmed, nulls included
    assert data["warnings"] == []  # an empty list is a value, not a null


def test_the_canvas_becomes_a_summary_and_says_how_to_read_the_rest() -> None:
    data = with_compact(_inv(), _figure_add_result())
    summary = data["canvas_summary"]
    assert summary["pages"] == 2
    assert summary["figures"][0] == {"id": "f0", "kind": "hbar", "title": "Chart 0", "page": "p1"}
    assert len(summary["figures"]) == 12
    compact = data["compact"]
    assert compact["omitted"] == ["canvas", "plan", "specs"]
    assert compact["read_with"] == "mammoth dashboard canvas get 7"
    assert FULL_FLAG in compact["full"]
    assert "canvas" not in data and "plan" not in data and "specs" not in data


def test_null_only_fields_are_dropped() -> None:
    data = with_compact(_inv(), {"figure_id": "f1", "layout_key": None, "style": {"a": None}})
    assert data == {"figure_id": "f1"}


def test_full_returns_the_payload_unchanged() -> None:
    full = _figure_add_result()
    assert with_compact(_inv(full_output=True), full) is full


def test_dry_run_and_other_commands_are_unchanged() -> None:
    full = _figure_add_result()
    assert with_compact(_inv(dry_run=True), full) is full
    assert with_compact(_inv("dashboard.get"), full) is full


@pytest.mark.parametrize(
    "command_id",
    [
        "dashboard.figure.add",
        "dashboard.figure-intent",
        "dashboard.v3.generate",
        "dashboard.chat.edit",
        "dashboard.filter.add",
        "dashboard.canvas.restore",
        "dashboard.canvas.save",
    ],
)
def test_every_compacted_command_accepts_full(command_id: str) -> None:
    assert command_id in COMPACT_COMMANDS
    validate_extra_args(command_id, [FULL_FLAG])


def test_full_is_refused_where_nothing_is_compacted() -> None:
    with pytest.raises(CliError, match="Unknown option '--full'"):
        validate_extra_args("dashboard.get", [FULL_FLAG])


def test_a_canvas_nested_in_state_is_summarised_too() -> None:
    nested = {
        "dashboard_id": 7,
        "state": {
            "command": "dashboard canvas get",
            "data": {"canvas": {"pages": [{"id": "p1", "added": [_null_figure(1)]}]}},
        },
    }
    data = with_compact(_inv("dashboard.chat.edit"), nested)
    assert data["state"]["data"]["canvas_summary"]["pages"] == 1
    assert data["compact"]["omitted"] == ["state.data.canvas"]


def test_help_says_the_result_is_compact_and_names_full() -> None:
    from mammoth_cli.testing import make_runner

    text = " ".join(make_runner().invoke_help("dashboard figure add").split())
    assert "The result is compact" in text and FULL_FLAG in text
