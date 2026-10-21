"""CLI side of the PRD-3119 prod-log follow-ups: pure functions, no stand-ins."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.dataset import resolve_batch_columns
from mammoth_cli.commands.view import keep_columns
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.strict import apply_input_aliases
from mammoth_cli.services.conditions import compile_condition

PAGE = {
    "columns": ["Name", "Age", "City"],
    "data": [{"Name": "A", "Age": 1, "City": "X"}, {"Name": "B", "Age": 2, "City": "Y"}],
}


def test_keep_columns_keeps_only_the_named_columns_in_rows_and_header() -> None:
    kept = keep_columns(PAGE, ["City", "Name"])

    assert kept["columns"] == ["City", "Name"]
    assert [list(row) for row in kept["data"]] == [["City", "Name"], ["City", "Name"]]


def test_keep_columns_without_columns_returns_the_page_unchanged() -> None:
    assert keep_columns(PAGE, None) is PAGE


def test_keep_columns_names_the_available_columns_for_a_typo() -> None:
    with pytest.raises(CliError) as caught:
        keep_columns(PAGE, ["Nme"])

    assert caught.value.code == "unknown_column"
    assert caught.value.details["available"] == ["Name", "Age", "City"]


@pytest.mark.parametrize("operator", ["REGEX", "regexp", "RLIKE"])
def test_a_regex_operator_is_answered_with_what_works(operator: str) -> None:
    with pytest.raises(CliError) as caught:
        compile_condition({"column": "Name", "operator": operator, "value": "^A"})

    assert caught.value.code == "invalid_condition"
    assert "CONTAINS" in (caught.value.hint or "")
    assert "substring" in (caught.value.hint or "")


SCHEMA = [{"c_id": "column_1", "c_name": "Name"}, {"c_id": "column_2", "c_name": "Age"}]


def test_batch_columns_turn_display_names_into_ids() -> None:
    assert resolve_batch_columns(SCHEMA, 7, ["Name", "column_2"]) == "column_1,column_2"


def test_batch_columns_take_one_comma_separated_string() -> None:
    assert resolve_batch_columns(SCHEMA, 7, "Name, Age") == "column_1,column_2"


def test_batch_columns_refuse_an_unknown_name_with_the_known_ones() -> None:
    with pytest.raises(CliError) as caught:
        resolve_batch_columns(SCHEMA, 7, ["Nope"])

    assert caught.value.code == "unknown_column"
    assert caught.value.details["available"] == ["Age", "Name"]


def test_generate_params_written_at_the_top_level_are_nested_into_the_body() -> None:
    document: dict[str, object] = {"intent": "sales by region", "dataview_id": 5}

    apply_input_aliases("dashboard.v3.generate", document)

    assert document == {"body": {"params": {"intent": "sales by region", "dataview_id": 5}}}


def test_an_explicit_generate_body_is_left_alone() -> None:
    document: dict[str, object] = {"body": {"params": {"intent": "x"}}, "title": "t"}

    apply_input_aliases("dashboard.v3.generate", document)

    assert document["body"] == {"params": {"intent": "x"}}


def test_download_format_is_an_alias_of_file_type() -> None:
    document: dict[str, object] = {"format": "xlsx"}

    apply_input_aliases("view.export.download", document)

    assert document == {"file_type": "xlsx"}


def test_export_csv_stays_csv_and_download_takes_the_other_formats() -> None:
    csv = command_by_id("view.export.csv")
    download = command_by_id("view.export.download")

    assert csv is not None and download is not None
    assert csv["sdk_symbol"].endswith("ExportsAPI.to_csv")
    assert download["sdk_symbol"].endswith("ExportsAPI.to_file")
