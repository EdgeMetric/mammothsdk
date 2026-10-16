"""A month bucket is `year_month_number`, and the docs say why.

Extract Date's `year_month` writes "2026, October", which a chart axis sorts
alphabetically (changelog analytics build, 2026-10-15). Ruling (Gaurav,
2026-10-16): the component stays, and the CLI's guidance defaults month buckets
to `year_month_number` ("2026-10").
"""

from __future__ import annotations

from pathlib import Path

from mammoth_cli.manifest.loader import command_by_id

_RECIPE = (
    Path(__file__).resolve().parents[2]
    / "mammoth_cli"
    / "bundled_skill"
    / "mammoth-cli"
    / "references"
    / "recipes"
    / "dashboards.md"
)


def test_extract_date_names_year_month_number_for_a_month_bucket() -> None:
    record = command_by_id("view.transform.extract-date")
    restrictions = record["known_restrictions"]
    assert "For a month bucket use `year_month_number`" in restrictions
    assert "sorts alphabetically" in restrictions


def test_the_dashboards_recipe_charts_months_with_year_month_number() -> None:
    text = _RECIPE.read_text(encoding="utf-8")
    assert "## A month axis" in text
    assert "`year_month_number`" in text and "sorts it alphabetically" in text
