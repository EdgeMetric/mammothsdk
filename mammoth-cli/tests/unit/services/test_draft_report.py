"""The sample reports on connector draft reads (issues #356 and #357)."""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.draft_report import _cap_note, with_each_reports


def _draft(each: dict[str, Any], parent_rows: int | None = 76) -> dict[str, Any]:
    return {
        "id": 9,
        "sources": [
            {"id": "s1", "name": "invoice_run", "row_count": parent_rows},
            {"id": "s2", "name": "invoices", "each": {"source_id": "s1", **each}},
        ],
    }


def test_a_capped_each_names_the_real_parent_count() -> None:
    out = with_each_reports(_draft({"capped": True, "failed": 3, "read": 17, "total": 20}))

    each = out["sources"][1]["each"]
    assert each["summary"] == "sampled 20 of 76 parents; 17 read, 3 failed"
    assert each["sampled"] == 20
    assert each["parents_total"] == 76
    # The server's own keys are kept as they were.
    assert each["total"] == 20


def test_a_capped_each_with_no_known_parent_count_says_so() -> None:
    out = with_each_reports(_draft({"capped": True, "failed": 3, "read": 17, "total": 20}, None))

    each = out["sources"][1]["each"]
    assert each["summary"] == "capped at 20 parents, total unknown; 17 read, 3 failed"
    assert each["parents_total"] is None


def test_an_each_that_names_no_known_parent_has_no_total() -> None:
    draft = _draft({"capped": True, "total": 20})
    draft["sources"][1]["each"]["source_id"] = "elsewhere"

    each = with_each_reports(draft)["sources"][1]["each"]

    assert each["summary"] == "capped at 20 parents, total unknown"


def test_an_unrelated_each_value_equal_to_a_sibling_name_is_not_taken_for_the_parent() -> None:
    draft = _draft({"capped": True, "total": 20, "label": "invoice_run"})
    draft["sources"][1]["each"]["source_id"] = "elsewhere"

    each = with_each_reports(draft)["sources"][1]["each"]

    assert each["parents_total"] is None
    assert each["summary"] == "capped at 20 parents, total unknown"


def test_a_key_that_contains_parent_names_the_parent() -> None:
    draft = _draft({"capped": True, "total": 20, "parent_source": "invoice_run"})
    draft["sources"][1]["each"]["source_id"] = "elsewhere"

    each = with_each_reports(draft)["sources"][1]["each"]

    assert each["summary"] == "sampled 20 of 76 parents"


def test_an_uncapped_each_reads_all_its_parents() -> None:
    draft = _draft({"capped": False, "read": 5, "failed": 0, "total": 5})

    each = with_each_reports(draft)["sources"][1]["each"]

    assert each["summary"] == "read all 5 parents; 5 read, 0 failed"
    assert each["parents_total"] == 5


def test_a_draft_without_each_is_returned_as_it_was() -> None:
    draft = {"id": 9, "sources": [{"id": "s1", "name": "plain"}]}

    assert with_each_reports(draft) == draft
    assert with_each_reports(["not", "a", "draft"]) == ["not", "a", "draft"]


def test_a_preview_short_of_its_limit_on_a_bigger_source_is_marked_capped() -> None:
    preview = {"rows": [{}] * 10, "row_count": 10}

    out = _cap_note(preview, 100, {"id": "s19", "row_count": 76})

    assert out["capped"] is True
    assert out["limit_requested"] == 100
    assert out["limit_applied"] == 10
    assert out["source_row_count"] == 76
    assert "sample" in out["hint"]


def test_a_preview_of_a_small_source_is_not_capped() -> None:
    preview = {"rows": [{}] * 10, "row_count": 10}

    assert _cap_note(preview, 100, {"id": "s19", "row_count": 10}) == preview


def test_has_more_marks_a_short_preview_capped_without_a_row_count() -> None:
    out = _cap_note({"rows": [{}] * 10}, 100, {"has_more": True})

    assert out["capped"] is True
    assert "source_row_count" not in out


def test_a_parent_read_to_its_limit_gives_no_total() -> None:
    """The server sets has_more on a source read to its limit; its row_count is a floor."""
    draft = _draft({"capped": True, "failed": 3, "read": 17, "total": 20})
    draft["sources"][0]["has_more"] = True

    each = with_each_reports(draft)["sources"][1]["each"]

    assert each["parents_total"] is None
    assert each["summary"] == "capped at 20 parents, total unknown; 17 read, 3 failed"


def test_a_parent_not_read_to_its_limit_keeps_its_total() -> None:
    draft = _draft({"capped": True, "total": 20})
    draft["sources"][0]["has_more"] = False

    assert with_each_reports(draft)["sources"][1]["each"]["parents_total"] == 76
