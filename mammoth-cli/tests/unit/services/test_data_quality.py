"""Column warnings from a data page: text columns holding numbers or dates, blanks."""

from __future__ import annotations

import json
from typing import Any

from mammoth_cli.services.data_quality import column_warnings


def _rows(values: list[object], column: str = "price") -> list[dict[str, object]]:
    return [{column: v} for v in values]


def _variant_warning(rows: list[dict[str, object]], view_id: int | None = None) -> dict[str, Any]:
    (warning,) = [
        w
        for w in column_warnings(rows, {"brand": "TEXT"}, view_id=view_id)
        if w["issue"] == "variant_spellings"
    ]
    return warning


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


def test_dates_stored_as_text_does_not_claim_unrecognized_values_go_empty() -> None:
    """Truth-probe finding: ``_DATE_FORMATS`` is a narrow whitelist (no
    ``%d-%b-%Y`` etc.), so a value like ``15-Jan-2024`` lands in ``others``
    purely because the CLI's own check doesn't recognize it -- not because
    the backend's date converter can't parse it. The probe confirmed such
    values convert losslessly, so the warning must not assert they'll come
    back empty.
    """
    rows = _rows(
        [
            "2026-01-02",
            "2026-02-03",
            "2026-03-04",
            "2026-04-05",
            "2026-05-06",
            "15-Jan-2024",
        ],
        column="day",
    )
    (warning,) = column_warnings(rows, {"day": "TEXT"})
    assert warning["issue"] == "dates_stored_as_text"
    assert "'15-Jan-2024'" in warning["detail"]
    assert "makes them empty" not in warning["detail"]


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


def _benchmark(cpm: object, reach: object = "62.0") -> dict[str, object]:
    return {"market": "Mumbai", "cpm_inr": cpm, "max_reach_pct": reach}


_BENCHMARK_TYPES = {"market": "TEXT", "cpm_inr": "NUMERIC", "max_reach_pct": "NUMERIC"}


def test_a_blank_in_the_only_varying_number_offers_removing_the_rows() -> None:
    """Eval T2-WPP-W7: a benchmark row whose one varying figure is blank holds
    no figure at all. The warning offered fill, remove or keep as equals and
    the agent kept both rows (24, not the 22 a clean-up leaves)."""
    rows = [_benchmark("150"), _benchmark(None), _benchmark("145")]
    (warning,) = column_warnings(rows, _BENCHMARK_TYPES, view_id=3428, dataset_id=2791)
    assert "only number that varies" in warning["detail"]
    spec = {"condition": {"column": "cpm_inr", "operator": "IS_NOT_EMPTY"}, "dataset_id": 2791}
    assert warning["fix"] == f"mammoth view transform filter 3428 --input '{json.dumps(spec)}'"


def test_a_blank_beside_another_varying_number_keeps_the_open_choice() -> None:
    """A row that still carries another figure is not empty, so nothing is
    recommended: dropping it would lose that figure."""
    rows = [_benchmark("150", "62"), _benchmark(None, "55"), _benchmark("145", "60")]
    (warning,) = column_warnings(rows, _BENCHMARK_TYPES, view_id=3428, dataset_id=2791)
    assert warning["detail"].endswith("or keep them and say so.")
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


def test_variant_spellings_are_grouped_with_a_bulk_replace_fix() -> None:
    rows = _rows(["PEPSI", "Pepsi ", "pepsi", "Pepsi", "Pepsi", "Coke", "Sprite"], column="brand")
    warning = _variant_warning(rows, view_id=62)
    assert "{'PEPSI', 'Pepsi', 'Pepsi ', 'pepsi'} -> 'Pepsi'" in warning["detail"]
    assert warning["fix"].startswith("mammoth view transform bulk-replace 62 --input ")
    payload = json.loads(warning["fix"].split("--input ", 1)[1].strip("'"))
    assert payload["columns"] == ["brand"]
    (mapping,) = payload["mapping"]
    assert sorted(mapping["search"]) == ["PEPSI", "Pepsi", "Pepsi ", "pepsi"]
    assert mapping["replace"] == "Pepsi"


def test_variant_spellings_placeholder_view_id_when_unknown() -> None:
    rows = _rows(["PEPSI", "Pepsi ", "pepsi"], column="brand")
    warning = _variant_warning(rows)
    assert warning["fix"].startswith("mammoth view transform bulk-replace VIEW_ID --input ")


def test_variant_spellings_do_not_fuzzy_match_different_words() -> None:
    """'pepsi cola' is a different brand name, not a spelling of 'pepsi': only
    values that are normalisation-equal (same case-, whitespace- and
    punctuation-stripped key) may be grouped.
    """
    rows = _rows(
        ["pepsi", "Pepsi", "pepsi cola", "pepsi cola", "sprite", "sprite"],
        column="brand",
    )
    warning = _variant_warning(rows)
    payload = json.loads(warning["fix"].split("--input ", 1)[1].strip("'"))
    searched = {v for m in payload["mapping"] for v in m["search"]}
    assert searched == {"pepsi", "Pepsi"}
    assert "pepsi cola" not in searched


def test_variant_spellings_ignores_inner_punctuation_differences() -> None:
    rows = _rows(["Pepsi, Co.", "Pepsi Co", "pepsi co"], column="brand")
    warning = _variant_warning(rows)
    payload = json.loads(warning["fix"].split("--input ", 1)[1].strip("'"))
    (mapping,) = payload["mapping"]
    assert sorted(mapping["search"]) == ["Pepsi Co", "Pepsi, Co.", "pepsi co"]


def test_variant_spellings_caps_at_five_groups_and_says_so() -> None:
    values: list[object] = []
    for i in range(6):
        values.extend([f"Brand{i}", f"brand{i} "])
    rows = _rows(values, column="brand")
    warning = _variant_warning(rows, view_id=1)
    payload = json.loads(warning["fix"].split("--input ", 1)[1].strip("'"))
    assert len(payload["mapping"]) == 5
    assert "1 more" in warning["detail"]


def test_no_variant_spellings_is_quiet_for_distinct_words() -> None:
    rows = _rows(["Coke", "Sprite", "Fanta"], column="brand")
    assert [
        w for w in column_warnings(rows, {"brand": "TEXT"}) if w["issue"] == "variant_spellings"
    ] == []


def test_variant_spellings_replace_with_the_most_used_real_spelling() -> None:
    rows = _rows(["McDonald's", "McDonald's", "mcdonald's", "Kfc", "Taco"], column="brand")
    warning = _variant_warning(rows, view_id=7)

    assert '-> "McDonald\'s"' in warning["detail"]
    assert "Mcdonald'S" not in warning["fix"]


_STORE_TYPES = {"date": "DATE", "store": "TEXT"}


def _store_rows(*spans: tuple[str, list[str]]) -> list[dict[str, object]]:
    return [{"date": day, "store": store} for store, days in spans for day in days]


def test_a_label_that_stops_where_a_longer_one_starts_reads_as_a_rename() -> None:
    """A store renamed in March ("Riverside" -> "Riverside Mall") splits its figures
    across two names; the agent asked and kept them apart, so the quarter showed
    no drop where the real one was (eval T2-BK-G3)."""
    rows = _store_rows(
        ("Riverside", ["2026-01-05", "2026-02-11", "2026-02-27"]),
        ("Riverside Mall", ["2026-03-02", "2026-03-22"]),
        ("Downtown", ["2026-01-14", "2026-03-22"]),
    )

    (warning,) = [
        w for w in column_warnings(rows, _STORE_TYPES, view_id=62) if w["issue"] == "renamed_label"
    ]

    assert warning["column"] == "store"
    assert "'Riverside'" in warning["detail"] and "'Riverside Mall'" in warning["detail"]
    assert warning["fix"] == (
        "mammoth view transform bulk-replace 62 --input "
        '\'{"columns": ["store"], "mapping": [{"search": ["Riverside"], '
        '"replace": "Riverside Mall"}]}\''
    )


def test_labels_that_share_dates_are_not_a_rename() -> None:
    rows = _store_rows(
        ("Pepsi", ["2026-01-05", "2026-03-01"]),
        ("Pepsi Max", ["2026-02-01", "2026-03-22"]),
    )

    assert not [
        w
        for w in column_warnings(rows, {"date": "DATE", "store": "TEXT"})
        if w["issue"] == "renamed_label"
    ]
