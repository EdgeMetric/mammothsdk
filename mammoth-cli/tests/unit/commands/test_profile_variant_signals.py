"""``view data profile`` says which columns it compared for spelling variants."""

from __future__ import annotations

from mammoth_cli.commands.view_profile import _Scope, _variant_report
from mammoth_cli.services import data_profile as dp


def _scope() -> _Scope:
    return _Scope(
        service=None,
        dataset_id=9,
        view_id=7,
        project_id=1,
        internal={"name": "column_1", "qty": "column_2", "id": "column_3", "one": "column_4"},
        types={"name": "TEXT", "qty": "NUMERIC", "id": "TEXT", "one": "TEXT"},
    )


def test_checked_and_skipped_columns_are_named_with_reasons() -> None:
    tables = {
        "name": {"Acme Ltd": 3, "ACME Limited": 2, "Zed": 1},
        "id": None,
    }
    report, checked, skipped = _variant_report(_scope(), ["name", "qty", "id", "one"], tables)
    assert [r["column"] for r in report] == ["name"]
    assert checked == ["name"]
    reasons = {s["column"]: s["reason"] for s in skipped}
    assert reasons["qty"] == "type is NUMERIC, not TEXT"
    assert str(dp.MAX_LISTED_DISTINCT) in reasons["id"]
    assert "not listed" in reasons["one"]


def test_a_clean_text_column_is_checked_not_skipped() -> None:
    report, checked, skipped = _variant_report(_scope(), ["name"], {"name": {"Acme": 3, "Zed": 1}})
    assert report == [] and checked == ["name"] and skipped == []
