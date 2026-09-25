"""Tests for the dashboard deliverable check (money shown, blanks decided)."""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.dashboard_review import profiles_from_view, review, upload_hints

# The profile the dashboard backend computed for the eval's orders view.
_PROFILES = [
    {"name": "order_id", "type": "dimension", "identifier": True},
    {"name": "product", "type": "dimension"},
    {"name": "segment", "type": "dimension", "nullRate": 0.05},
    {"name": "qty", "type": "measure", "semantic": "count", "nullRate": 0.025},
    {"name": "price", "type": "measure", "perUnit": True, "semantic": "score", "nullRate": 0.1},
]


def _doc(pages: list[dict[str, Any]], profiles: list[dict[str, Any]] | None = None) -> Any:
    return {
        "canvas": {"dataset": {"dataview_id": 81}, "pages": pages, "derived": []},
        "plan": {"hints": {"_profiles": _PROFILES if profiles is None else profiles}},
    }


def _issues(warnings: list[dict[str, Any]]) -> list[str]:
    return [w["issue"] for w in warnings]


def test_counts_only_board_is_told_to_add_revenue_with_the_exact_command() -> None:
    board = _doc([{"id": "p1", "added": [{"kind": "hbar", "dim": "product", "measure": "qty"}]}])
    warnings = review(board, dataset_id=84)
    money = next(w for w in warnings if w["issue"] == "money_not_shown")
    assert "qty * price" in money["detail"]
    assert money["fix"] == (
        "mammoth view transform math 81 --input "
        '\'{"dataset_id": 84, "expression": "qty * price", "new_column": "revenue"}\''
    )


def test_summing_a_unit_price_is_flagged() -> None:
    board = _doc(
        [
            {
                "id": "p1",
                "added": [{"kind": "hbar", "dim": "segment", "measure": "price", "agg": "sum"}],
            }
        ]
    )
    assert "unit_price_summed" in _issues(review(board))
    assert "money_not_shown" not in _issues(review(board))


def test_a_board_that_charts_revenue_gets_no_money_warning() -> None:
    profiles = [*_PROFILES, {"name": "revenue", "type": "measure"}]
    board = _doc(
        [
            {
                "id": "p1",
                "focus": {"measure": "revenue", "kpis": [{"field": "revenue", "agg": "sum"}]},
            }
        ],
        profiles,
    )
    assert not {"money_not_shown", "unit_price_summed"} & set(_issues(review(board)))


def test_blanks_are_reported_for_the_columns_the_board_shows() -> None:
    board = _doc([{"id": "p1", "added": [{"kind": "hbar", "dim": "segment", "measure": "qty"}]}])
    blanks = [w["column"] for w in review(board) if w["issue"] == "blank_values"]
    assert blanks == ["segment", "qty"]


def test_an_empty_board_lists_every_blank_column() -> None:
    blanks = [w["column"] for w in review(_doc([{"id": "p1"}])) if w["issue"] == "blank_values"]
    assert blanks == ["segment", "qty", "price"]


def test_no_profile_means_no_advice() -> None:
    assert review(_doc([{"id": "p1"}], profiles=[])) == []
    assert review({"canvas": None}) == []


def test_profiles_from_view_types_columns_and_measures_blanks() -> None:
    metadata = [
        {"display_name": "product", "type": "TEXT"},
        {"display_name": "qty", "type": "NUMERIC"},
        {"display_name": "day", "type": "DATE"},
    ]
    rows = [{"product": "a", "qty": 1}, {"product": " ", "qty": None}, {"product": "c", "qty": 3}]
    assert profiles_from_view(metadata, rows) == [
        {"name": "product", "type": "dimension", "nullRate": 1 / 3},
        {"name": "qty", "type": "measure", "nullRate": 1 / 3},
        {"name": "day", "type": "date"},
    ]


def test_upload_hints_name_revenue_before_any_dashboard_and_leave_blanks_out() -> None:
    metadata = [
        {"display_name": "qty", "type": "NUMERIC"},
        {"display_name": "price", "type": "NUMERIC"},
    ]
    hints = upload_hints(81, metadata, [{"qty": 2, "price": None}], dataset_id=84)
    assert _issues(hints) == ["money_not_shown"]
    assert hints[0]["fix"] == (
        "mammoth view transform math 81 --input "
        '\'{"dataset_id": 84, "expression": "qty * price", "new_column": "revenue"}\''
    )
