"""Pure logic behind ``dataset list --input '{"name": ...}'`` and its paging guard."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.dataset import _validate_paging
from mammoth_cli.errors.envelope import CliError, missing_project_error
from mammoth_cli.services.listing import name_matches, search_page

_RECORDS = [
    {"id": 1, "name": "Sales_2024.csv", "data_schema": [{"c_name": "A", "c_type": "TEXT"}]},
    {"id": 2, "name": "inventory.csv"},
    {"id": 3, "name": "sales summary", "data_schema": [{"c_name": "B", "c_type": "NUMERIC"}]},
    {"id": 4, "name": None},
]


def test_name_matches_is_a_case_insensitive_substring() -> None:
    assert [r["id"] for r in name_matches(_RECORDS, "SALES")] == [1, 3]
    assert name_matches(_RECORDS, "nothing-like-this") == []


def test_search_page_rows_carry_no_column_lists() -> None:
    page = search_page(_RECORDS, "sales", offset=0, limit=None)
    assert [row["id"] for row in page["datasets"]] == [1, 3]
    assert all("columns" not in row for row in page["datasets"])
    assert page["matched"] == 2 and "more" not in page


def test_search_page_pages_over_matches_not_over_the_project() -> None:
    page = search_page(_RECORDS, "s", offset=0, limit=1)
    assert [row["id"] for row in page["datasets"]] == [1]
    assert page["more"] is True and page["next_offset"] == 1


def test_search_page_is_not_cut_to_thirteen_rows() -> None:
    many = [{"id": n, "name": f"report {n}"} for n in range(60)]
    assert len(search_page(many, "report", offset=0, limit=None)["datasets"]) == 60


def test_project_required_points_at_dataset_find() -> None:
    assert "mammoth dataset find SUBSTRING" in missing_project_error().recovery_commands


@pytest.mark.parametrize("payload", [{"limit": 1000}, {"limit": 101}, {"offset": -1}])
def test_list_paging_is_refused_before_any_call(payload: dict[str, int]) -> None:
    with pytest.raises(CliError) as excinfo:
        _validate_paging(payload)
    assert excinfo.value.code == "invalid_argument"


def test_limit_100_is_accepted() -> None:
    _validate_paging({"limit": 100, "offset": 0})
