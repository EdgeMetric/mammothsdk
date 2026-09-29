"""Stored column stats: read from the backend's profile payload shape, staleness by row count."""

from __future__ import annotations

from mammoth_cli.services import data_profile as dp
from mammoth_cli.services import stored_stats


def _entry(name: str, unique: int, missing: int, empty: int, rows: int) -> dict[str, object]:
    return {
        "column_name": name,
        "schema_analysis": {"num_unique": unique},
        "statistical_summary": {"data_sample": ["a", "b"]},
        "quality_metrics": {"empty_string_count": empty},
        "performance_metadata": {"missing_count": missing, "total_rows": rows},
    }


def test_facts_are_keyed_by_display_name_and_sum_blank_kinds() -> None:
    payload = {"profile": {"c1": _entry("city", 3, 4, 2, 100)}, "join_suggestions": []}
    facts, rows = stored_stats.stored_facts(payload, {"City": "c1", "Other": "c2"})
    assert rows == 100
    assert facts == {"City": {"distinct": 3, "nulls": 6, "sample": ["a", "b"]}}


def test_stale_when_row_counts_differ() -> None:
    result = stored_stats.currency(100, 90)
    assert result["current"] is False
    assert "100" in result["reason"] and "90" in result["reason"]


def test_current_states_its_limit() -> None:
    result = stored_stats.currency(100, 100)
    assert result["current"] is True
    assert "as-of" in result["note"]


def test_unknown_row_count_is_not_current() -> None:
    assert stored_stats.currency(None, 5)["current"] is False


def test_standardized_difference_direction_and_size() -> None:
    d = dp.standardized_difference(
        {"n": 50, "mean": 12.0, "stddev": 2.0}, {"n": 50, "mean": 10.0, "stddev": 2.0}
    )
    assert d == 1.0
    assert (
        dp.standardized_difference(
            {"n": 1, "mean": 1, "stddev": 1}, {"n": 9, "mean": 2, "stddev": 1}
        )
        is None
    )
    assert (
        dp.standardized_difference(
            {"n": 5, "mean": 1, "stddev": None}, {"n": 9, "mean": 2, "stddev": 1}
        )
        is None
    )
