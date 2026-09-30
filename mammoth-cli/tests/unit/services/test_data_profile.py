"""Rules of the whole-view profile, run on plain values (no server, no doubles)."""

from __future__ import annotations

import pytest

from mammoth_cli.services import data_profile as dp


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("Acme Ltd", "ACME Limited"),
        ("Acme Ltd.", "acme limited"),
        ("Acme L.T.D.", "Acme Limited"),
        ("Smith & Sons Inc", "Smith and Sons Incorporated"),
        ("Red Frog Hire Limited", "Red  Frog  Hire  LTD"),
        ("Kainos Corp.", "Kainos Corporation"),
    ],
)
def test_legal_form_spellings_share_a_key(a: str, b: str) -> None:
    assert dp.spelling_key(a) == dp.spelling_key(b)


@pytest.mark.parametrize(
    ("a", "b"),
    [("Acme Ltd", "Acme"), ("Acme Ltd", "Acme Holdings Ltd"), ("Pepsi", "Pepsi Cola")],
)
def test_different_names_never_share_a_key(a: str, b: str) -> None:
    assert dp.spelling_key(a) != dp.spelling_key(b)


def test_variant_groups_keep_the_most_frequent_spelling_and_emit_a_mapping() -> None:
    counts = {
        "Red Frog Hire Limited": 40,
        "Red Frog Hire Ltd": 7,
        "RED FROG HIRE LTD.": 2,
        "Other": 9,
    }
    groups = dp.variant_groups(counts)

    assert len(groups) == 1
    assert groups[0]["keep"] == "Red Frog Hire Limited"
    assert groups[0]["rows"] == 49
    assert dp.bulk_replace_input("Supplier", groups)["mapping"] == [
        {"search": ["Red Frog Hire Ltd", "RED FROG HIRE LTD."], "replace": "Red Frog Hire Limited"}
    ]


def test_a_single_spelling_is_not_a_group() -> None:
    assert dp.variant_groups({"Acme Ltd": 3, "Beta Inc": 2, None: 5, "": 1}) == []  # type: ignore[dict-item]


# Supplier names from the World Bank Argentina awards file QA replayed (UQA-RT3-01): a name with
# and without its legal form, and with an extra "DE", is one supplier the sure groups missed.
_AWARD_NAMES = {
    "TECNOLAB S.A.": 3,
    "TECNOLAB SA": 2,
    "TECNOLAB": 2,
    "APPLIED BIOSYSTEMS SA": 1,
    "APPLIED BIOSYSTEMS.": 1,
    "LATINOCONSULT S.A.": 2,
    "LATINOCONSULT": 1,
    "SIGMA-ALDRICH ARGENTINA S.A.": 2,
    "SIGMA-ALDRICH DE ARGENTINA S.R.L.": 1,
    "SIGMA-ALDRICH DE ARGENTINA SA": 1,
    "Acme Holdings SA": 4,
    "Acme SA": 3,
}


def test_likely_groups_join_a_name_with_and_without_its_legal_form() -> None:
    likely = {group["keep"]: group for group in dp.likely_groups(_AWARD_NAMES)}

    assert set(likely) == {
        "TECNOLAB S.A.",
        "APPLIED BIOSYSTEMS.",
        "LATINOCONSULT S.A.",
        "SIGMA-ALDRICH ARGENTINA S.A.",
    }
    assert [v["value"] for v in likely["TECNOLAB S.A."]["variants"]] == [
        "TECNOLAB S.A.",
        "TECNOLAB",
        "TECNOLAB SA",
    ]
    assert likely["SIGMA-ALDRICH ARGENTINA S.A."]["rows"] == 4


def test_likely_groups_never_join_a_different_name() -> None:
    groups = dp.likely_groups({"Acme Holdings SA": 4, "Acme SA": 3, "Pepsi": 2, "Pepsi Cola": 2})
    assert groups == []


def test_likely_groups_leave_out_what_the_sure_groups_already_join() -> None:
    assert dp.likely_groups({"Acme Ltd": 3, "ACME Limited": 2}) == []


def test_summarize_column_counts_null_and_blank_text_together() -> None:
    summary = dp.summarize_column({None: 6, "  ": 4, "a": 30, "b": 60}, total_rows=100, top=1)

    assert summary["nulls"] == 10
    assert summary["null_share"] == 0.1
    assert summary["top_values"] == [{"value": "b", "count": 60, "share": 0.6}]


def _cells(rate_a: float, rate_b: float, n: int = 1000) -> list[tuple[str, int, int]]:
    """Two predictor values, half of the rows each, with the given positive rates."""
    half = n // 2
    return [
        ("A", 1, round(half * rate_a)),
        ("A", -1, half - round(half * rate_a)),
        ("B", 1, round(half * rate_b)),
        ("B", -1, half - round(half * rate_b)),
    ]


def test_association_is_strong_for_a_column_that_decides_the_target() -> None:
    result = dp.association(_cells(1.0, 0.0), positive=1, total_rows=1000)
    assert result is not None
    assert result["cramers_v"] == 1.0


def test_association_is_zero_for_an_unrelated_column() -> None:
    result = dp.association(_cells(0.2, 0.2), positive=1, total_rows=1000)
    assert result is not None
    assert result["cramers_v"] == 0.0


def test_association_ranks_the_value_whose_rate_departs_most_first() -> None:
    result = dp.association(_cells(0.5, 0.1), positive=1, total_rows=1000)
    assert result is not None
    assert result["signals"][0]["rate"] == 0.5
    assert result["signals"][0]["lift"] == pytest.approx(1.67, abs=0.01)


def test_blank_versus_filled_rate_is_reported_when_the_column_has_blanks() -> None:
    cells = [(None, 1, 30), (None, -1, 10), ("x", 1, 20), ("x", -1, 140)]
    result = dp.association(cells, positive=1, total_rows=200)
    assert result is not None
    assert result["blank_vs_filled"] == {
        "blank_rows": 40,
        "blank_rate": 0.75,
        "filled_rows": 160,
        "filled_rate": 0.125,
    }


def test_association_needs_two_values_and_two_classes() -> None:
    assert dp.association([("A", 1, 5), ("A", -1, 5)], positive=1, total_rows=10) is None
    assert dp.association([("A", 1, 5), ("B", 1, 5)], positive=1, total_rows=10) is None


def test_positive_class_is_the_rarest() -> None:
    assert dp.choose_positive({1: 3672, -1: 46328}) == 1


def test_churn_file_rate_is_seven_point_three_four_percent() -> None:
    classes = {1: 3672, -1: 46328}
    positive = dp.choose_positive(classes)
    assert round(classes[positive] / sum(classes.values()), 4) == 0.0734
