"""Column warnings from a data page: text columns holding numbers or dates, blanks."""

from __future__ import annotations

from mammoth_cli.services.data_quality import column_warnings


def _rows(values: list[object], column: str = "price") -> list[dict[str, object]]:
    return [{column: v} for v in values]


def test_numbers_stored_as_text_names_the_odd_values_and_the_fix() -> None:
    rows = _rows(["30.00", "12.50", "7.25", "N/A", "4.00"])
    (warning,) = column_warnings(rows, {"price": "TEXT"}, view_id=62)
    assert warning["issue"] == "numbers_stored_as_text"
    assert "4 of 5 non-blank values are numbers" in warning["detail"]
    assert "'N/A'" in warning["detail"]
    assert warning["fix"] == (
        "mammoth view transform convert-type 62 --input "
        '\'{"conversions": [{"column": "price", "to": "NUMERIC"}]}\''
    )


def test_money_and_percent_text_counts_as_numbers() -> None:
    rows = _rows(["$1,200.50", "15%", "-3", ".5"])
    assert column_warnings(rows, {"price": "TEXT"})[0]["issue"] == "numbers_stored_as_text"


def test_dates_stored_as_text() -> None:
    rows = _rows(["2026-01-02", "2026-02-03", "03/04/2026"], column="day")
    (warning,) = column_warnings(rows, {"day": "TEXT"})
    assert warning["issue"] == "dates_stored_as_text"
    assert '"to": "DATE"' in warning["fix"]


def test_mostly_text_and_typed_columns_are_quiet() -> None:
    assert column_warnings(_rows(["a", "b", "1", "c"]), {"price": "TEXT"}) == []
    assert column_warnings(_rows(["1", "2", "3"]), {"price": "NUMERIC"}) == []
    # Too few values to call a pattern.
    assert column_warnings(_rows(["1", "2"]), {"price": "TEXT"}) == []


def test_blank_values_are_counted_for_any_type() -> None:
    rows = _rows([None, "", "5", "6"], column="qty")
    (warning,) = column_warnings(rows, {"qty": "NUMERIC"})
    assert warning["issue"] == "blank_values"
    assert warning["detail"].startswith("2 of 4 rows are blank")
    assert "fix" not in warning


def test_no_rows_no_warnings() -> None:
    assert column_warnings([], {"price": "TEXT"}) == []


def test_exact_duplicate_rows_are_flagged_with_a_scoped_count_and_fix() -> None:
    """PR25 item I: two agent runs missed duplicate rows because
    ``column_warnings`` only ever checked individual columns, never whether
    the page itself held repeated rows. The count must be scoped to the rows
    actually read (never claimed table-wide), and the fix must be a directly
    runnable ``discard-duplicates`` command when the dataset id is known.
    """
    rows = [
        {"order_id": "1", "amount": "10"},
        {"order_id": "2", "amount": "20"},
        {"order_id": "1", "amount": "10"},  # exact duplicate of row 0
        {"order_id": "1", "amount": "10"},  # exact duplicate of row 0
    ]
    warnings = column_warnings(rows, {"order_id": "TEXT", "amount": "NUMERIC"}, view_id=62)
    (warning,) = [w for w in warnings if w["issue"] == "duplicate_rows"]
    assert warning["detail"] == (
        "2 of the 4 rows read are exact duplicates of another row in this page "
        "(not checked table-wide)."
    )
    assert "fix" not in warning
    assert warning["rows_checked"] == 4


def test_duplicate_rows_fix_is_a_runnable_command_when_dataset_id_is_known() -> None:
    rows = [{"a": "1"}, {"a": "1"}]
    (warning,) = column_warnings(rows, {"a": "TEXT"}, view_id=62, dataset_id=9)
    assert warning["issue"] == "duplicate_rows"
    assert warning["fix"] == (
        "mammoth view transform discard-duplicates 62 --input '{\"dataset_id\": 9}'"
    )


def test_no_duplicate_rows_is_quiet() -> None:
    rows = [{"a": "1"}, {"a": "2"}, {"a": "3"}]
    assert [w for w in column_warnings(rows, {"a": "TEXT"}) if w["issue"] == "duplicate_rows"] == []
