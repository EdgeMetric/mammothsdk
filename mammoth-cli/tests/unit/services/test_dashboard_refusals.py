"""Refused-card warnings are one per real miss and say what to do (bug bash 2026-10-15)."""

from __future__ import annotations

from mammoth_cli.commands.dashboard.generated import _reflect_not_applied
from mammoth_cli.services.dashboard_pages import generate_substitutions, refused_notes

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
