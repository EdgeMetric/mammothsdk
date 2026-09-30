"""Absence of a finding must be an explicit, checkable field, never silence."""

from __future__ import annotations

from mammoth_cli.commands.view import COLUMN_CHECK_ISSUES, _with_column_warnings


def test_clean_page_says_it_was_checked() -> None:
    data = {"data": [{"n": 1}, {"n": 2}, {"n": 3}]}
    out = _with_column_warnings(data, {"n": "NUMERIC"}, 7, 9)
    assert "column_warnings" not in out
    assert out["column_checks"] == {
        "scope": "page",
        "rows_checked": 3,
        "checked": list(COLUMN_CHECK_ISSUES),
        "found": 0,
    }


def test_findings_are_counted() -> None:
    rows = [{"price": v} for v in ("1.5", "2", "3", "4", "N/A")]
    out = _with_column_warnings({"data": rows}, {"price": "TEXT"}, 7, 9)
    assert out["column_checks"]["found"] == len(out["column_warnings"]) >= 1


def test_empty_page_reports_zero_rows_checked() -> None:
    out = _with_column_warnings({"data": []}, {"n": "NUMERIC"}, 7, 9)
    assert out["column_checks"]["rows_checked"] == 0
    assert out["column_checks"]["checked"] == []


def test_unknown_types_are_not_reported_as_checked() -> None:
    out = _with_column_warnings({"data": [{"n": 1}]}, {}, 7, 9)
    assert out["column_checks"]["checked"] == []
    assert out["column_checks"]["rows_checked"] == 1


class _Unprintable:
    def __str__(self) -> str:
        raise ValueError("cannot render")

    __repr__ = __str__


def test_a_check_that_throws_is_reported() -> None:
    rows = [{"n": _Unprintable()} for _ in range(4)]
    out = _with_column_warnings({"data": rows}, {"n": "TEXT"}, 7, 9)
    checks = out["column_checks"]
    assert checks["checked"] == []
    assert "cannot render" in checks["error"]
    assert checks["found"] == 0
