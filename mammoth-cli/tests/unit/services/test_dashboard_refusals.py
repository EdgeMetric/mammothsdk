"""Refused-card warnings are one per real miss and say what to do (bug bash 2026-10-15)."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.dashboard.generated import _reflect_not_applied
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.dashboard_pages import (
    append_figure,
    generate_substitutions,
    refused_asks,
    refused_notes,
)
from mammoth_cli.services.testing import FakeMammothService

_MESSAGE = (
    "Cards: Total Events and Total Pageviews.\n"
    "Couldn't do: SUM_events isn't a measure in this data; "
    "Daily Users - line; Daily Users - line.\n\n"
    "On the board: page 1 - KPI cards (Total Pageviews, Sum Users)"
)


def test_refused_notes_stop_at_the_end_of_the_couldnt_do_paragraph() -> None:
    assert refused_notes(_MESSAGE) == [
        "SUM_events isn't a measure in this data",
        "Daily Users - line",
        "Daily Users - line",
    ]


def test_each_miss_is_warned_once_and_names_the_fallback() -> None:
    warnings = generate_substitutions(None, {}, _MESSAGE)
    details = [w["detail"] for w in warnings]
    assert len(details) == 2
    assert not any("On the board" in d for d in details)
    measure = next(d for d in details if "SUM_events" in d)
    assert "dashboard figure add" in measure and '"measure": "SUM_events"' in measure


def test_changed_false_is_not_applied_and_does_not_echo_the_models_claim() -> None:
    data = {"changed": False, "bake_ok": False, "message": "I added a **Total Events** card."}
    out = _reflect_not_applied("dashboard.chat.edit", data, 744)
    assert out["message"].startswith("NOT APPLIED")
    assert out["model_message"] == "I added a **Total Events** card."
    assert "dashboard figure add 744" in " ".join(out["next_steps"])


def test_a_changed_edit_is_left_alone() -> None:
    data = {"changed": True, "message": "I added a card."}
    assert _reflect_not_applied("dashboard.chat.edit", data, 744) == data


def test_an_ask_that_did_not_land_is_a_warning() -> None:
    """Feedback 4 and 12 (2026-11-24): a refused ask must not read as a finished edit."""
    asks = [
        {"ask": "add a KPI", "status": "applied"},
        {"ask": "make it nicer", "status": "not checked"},
        {"ask": "show every bar", "status": "not done — the reply says it couldn't be"},
        {"ask": "split by key", "status": "held back"},
    ]
    assert [warning["detail"] for warning in refused_asks(asks)] == [
        "show every bar: not done — the reply says it couldn't be",
        "split by key: held back",
    ]
    assert refused_asks(None) == []


def test_an_edit_that_was_not_applied_names_the_route_of_a_second_view() -> None:
    data = {"changed": False, "bake_ok": False, "message": "Done."}
    out = _reflect_not_applied("dashboard.chat.edit", data, 744)
    assert "dashboard pages add 744" in " ".join(out["next_steps"])


def test_a_figure_of_another_source_names_the_pages_route() -> None:
    fake_service = FakeMammothService()
    symbol = "mammoth.api.dashboards.DashboardsAPI.append_figure"
    fake_service.responses[symbol] = CliError(
        code="conflict", message="no", details={"backend_code": "4DASH023"}
    )
    with pytest.raises(CliError) as excinfo:
        append_figure(fake_service, symbol, {"dashboard_id": 3, "dataview_id": 7})
    assert "dashboard pages add 3" in (excinfo.value.hint or "")
    assert '"dataview_id": 7' in (excinfo.value.hint or "")


def test_another_refusal_of_a_figure_keeps_its_own_hint() -> None:
    fake_service = FakeMammothService()
    symbol = "mammoth.api.dashboards.DashboardsAPI.append_figure"
    fake_service.responses[symbol] = CliError(code="conflict", message="no", hint="own")
    with pytest.raises(CliError) as excinfo:
        append_figure(fake_service, symbol, {"dashboard_id": 3, "dataview_id": 7})
    assert excinfo.value.hint == "own"
