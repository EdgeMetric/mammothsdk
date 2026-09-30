"""Read-only parsing of dates stored as TEXT: detect, state, and fail loud."""

from __future__ import annotations

from datetime import date

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import text_dates


def _format(values: list[str], requested: str | None = None) -> text_dates.TextDateFormat:
    return text_dates.detect_format(values, "Order Date", requested)


def test_month_first_is_detected_from_a_day_above_12_in_the_second_position() -> None:
    fmt = _format(["11/8/2017", "3/27/2018", "1/1/2014"])
    assert fmt.label == "M/D/YYYY"
    assert "27" in fmt.reason
    assert text_dates.parse_value("3/27/2018", fmt) == date(2018, 3, 27)


def test_day_first_is_detected_from_a_day_above_12_in_the_first_position() -> None:
    fmt = _format(["8/11/2017", "27/3/2018"])
    assert fmt.label == "D/M/YYYY"
    assert text_dates.parse_value("8/11/2017", fmt) == date(2017, 11, 8)


def test_day_month_ambiguity_fails_loud_and_names_the_way_out() -> None:
    with pytest.raises(CliError) as caught:
        _format(["1/2/2017", "3/4/2018", "12/12/2019"])
    assert "ambiguous" in caught.value.message
    assert "text_date_format" in (caught.value.hint or "")


def test_a_stated_order_settles_an_ambiguous_column() -> None:
    values = ["1/2/2017", "3/4/2018"]
    assert text_dates.parse_value("1/2/2017", _format(values, "D/M/YYYY")) == date(2017, 2, 1)
    assert text_dates.parse_value("1/2/2017", _format(values, "M/D/YYYY")) == date(2017, 1, 2)


def test_a_stated_order_the_data_contradicts_fails_loud() -> None:
    fmt = _format(["3/27/2018", "1/2/2017"], "D/M/YYYY")
    with pytest.raises(CliError) as caught:
        text_dates.parse_value("3/27/2018", fmt)
    assert "not a valid date" in caught.value.message


def test_a_value_that_is_not_a_date_fails_loud_with_examples() -> None:
    with pytest.raises(CliError) as caught:
        _format(["3/27/2018", "N/A", "unknown"])
    assert caught.value.details["unparseable_count"] == 2
    assert "N/A" in caught.value.details["unparseable_examples"]


def test_mixed_layouts_fail_loud() -> None:
    with pytest.raises(CliError) as caught:
        _format(["3/27/2018", "2018-03-27"])
    assert "mixes date layouts" in caught.value.message


def test_iso_and_month_name_layouts_need_no_order_guess() -> None:
    assert _format(["2018-03-27", "2018-03-01 10:00:00"]).label == "YYYY-MM-DD"
    named = _format(["27-Mar-2018", "5 Jan 2017"])
    assert text_dates.parse_value("27-Mar-2018", named) == date(2018, 3, 27)


def test_a_calendar_impossible_date_fails_loud() -> None:
    fmt = _format(["3/27/2018", "1/13/2018"])
    with pytest.raises(CliError):
        text_dates.parse_value("2/30/2018", fmt)


def test_blank_values_are_ignored_by_detection_and_parse_to_none() -> None:
    fmt = _format(["", None, "3/27/2018"])
    assert text_dates.parse_value("", fmt) is None


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        ("DAY", date(2018, 3, 8)),
        ("WEEK", date(2018, 3, 5)),
        ("MONTH", date(2018, 3, 1)),
        ("QUARTER", date(2018, 1, 1)),
        ("YEAR", date(2018, 1, 1)),
        ("DECADE", date(2010, 1, 1)),
    ],
)
def test_bucket_start_is_the_first_day_of_the_period(level: str, expected: date) -> None:
    assert text_dates.bucket_start(date(2018, 3, 8), level) == expected


def test_a_level_a_text_date_cannot_take_fails_loud() -> None:
    with pytest.raises(CliError):
        text_dates.require_level("AUTO")
    with pytest.raises(CliError):
        text_dates.require_level("HOUR")


def test_rebucket_merges_stored_values_into_months_per_function() -> None:
    fmt = _format(["3/27/2018", "3/1/2018", "4/2/2018"])
    days = text_dates.parse_all(["3/27/2018", "3/1/2018", "4/2/2018"], fmt)
    rows = [
        {"group_0": "3/27/2018", "group_1": "West", "agg_0": 10, "agg_1": 5, "agg_2": 2},
        {"group_0": "3/1/2018", "group_1": "West", "agg_0": 4, "agg_1": 9, "agg_2": 1},
        {"group_0": "4/2/2018", "group_1": "West", "agg_0": 1, "agg_1": 3, "agg_2": 7},
    ]
    merged = text_dates.rebucket(
        rows,
        date_key="group_0",
        other_keys=["group_1"],
        functions={"agg_0": "SUM", "agg_1": "MAX", "agg_2": "MIN"},
        days=days,
        level="MONTH",
    )
    by_month = {row["group_0"]: row for row in merged}
    assert by_month["2018-03-01"]["agg_0"] == 14
    assert by_month["2018-03-01"]["agg_1"] == 9
    assert by_month["2018-03-01"]["agg_2"] == 1
    assert by_month["2018-04-01"]["agg_0"] == 1


def test_observed_range_is_the_min_and_max_parsed_date() -> None:
    fmt = _format(["3/27/2018", "1/13/2014"])
    days = text_dates.parse_all(["3/27/2018", "1/13/2014", ""], fmt)
    assert text_dates.observed_range(days) == {"min": "2014-01-13", "max": "2018-03-27"}
    assert text_dates.observed_range({"": None}) is None


def test_in_range_values_returns_the_stored_strings_not_the_parsed_dates() -> None:
    fmt = _format(["3/27/2018", "1/13/2014"])
    days = text_dates.parse_all(["3/27/2018", "1/13/2014"], fmt)
    assert text_dates.in_range_values(days, lambda d: d >= date(2018, 1, 1)) == ["3/27/2018"]
