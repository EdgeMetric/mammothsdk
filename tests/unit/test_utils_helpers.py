"""mammoth.utils.helpers, checked against how the backend parses the same strings.

Oracles come from mvc-service ``apiv2/apiv2/common/utils.py``:
``validate_and_get_time_type`` (``%Y-%m-%dT%H:%M:%S.%fZ`` inside ``(from:'..',to:'..')``)
and ``validate_and_get_ids`` (``int()`` over a comma split).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from mammoth.utils import format_date_range, parse_job_ids, validate_file_path


def backend_parse_time_type(value: str) -> dict[str, datetime]:
    """Port of mvc-service ``validate_and_get_time_type`` (the server-side oracle)."""
    value = value.replace("(", "").replace(")", "")
    out: dict[str, datetime] = {}
    for token in value.split(","):
        parts = token.split(":")
        key = parts[0].strip().replace("'", "")
        assert key in ("from", "to"), key
        raw = ":".join(parts[1:]).replace("'", "").replace(" ", "").strip()
        out[key] = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%fZ")
    return out


class TestFormatDateRange:
    def test_naive_datetimes_get_a_z_suffix_the_backend_accepts(self) -> None:
        a = datetime(2026, 1, 2, 3, 4, 5, 678000)
        b = datetime(2026, 2, 3, 4, 5, 6, 1000)
        text = format_date_range(a, b)
        assert text == "(from:'2026-01-02T03:04:05.678000Z',to:'2026-02-03T04:05:06.001000Z')"
        assert backend_parse_time_type(text) == {"from": a, "to": b}

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: a datetime with whole seconds is sent without '.%f'; the backend's "
        "strptime('%Y-%m-%dT%H:%M:%S.%fZ') rejects it",
    )
    def test_whole_second_datetimes_are_accepted_by_the_backend(self) -> None:
        text = format_date_range(datetime(2026, 1, 2, 3, 4, 5), datetime(2026, 1, 3))
        backend_parse_time_type(text)

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: timezone-aware datetimes are sent with '+00:00', not the 'Z' the backend "
        "requires",
    )
    def test_aware_datetimes_are_accepted_by_the_backend(self) -> None:
        a = datetime(2026, 1, 2, 3, 4, 5, 6, tzinfo=UTC)
        text = format_date_range(a, a + timedelta(days=1))
        backend_parse_time_type(text)

    def test_aware_datetime_keeps_its_own_offset_and_gets_no_extra_z(self) -> None:
        tz = timezone(timedelta(hours=5, minutes=30))
        text = format_date_range(
            datetime(2026, 1, 2, 3, 4, 5, 6, tzinfo=tz), datetime(2026, 1, 2, tzinfo=UTC)
        )
        assert text == "(from:'2026-01-02T03:04:05.000006+05:30',to:'2026-01-02T00:00:00+00:00')"


class TestParseJobIds:
    def test_comma_separated_ids_with_spaces(self) -> None:
        assert parse_job_ids("10, 11 ,12") == [10, 11, 12]

    def test_single_id(self) -> None:
        assert parse_job_ids("7") == [7]

    @pytest.mark.parametrize("blank", ["", "   ", "\n"])
    def test_blank_means_no_ids(self, blank: str) -> None:
        assert parse_job_ids(blank) == []

    def test_non_integer_id_raises_with_the_offending_text(self) -> None:
        with pytest.raises(ValueError, match=r"Invalid job ID format: .*'abc'"):
            parse_job_ids("1,abc,3")

    def test_trailing_comma_is_an_error_like_the_backend(self) -> None:
        with pytest.raises(ValueError, match="Invalid job ID format"):
            parse_job_ids("1,2,")


class TestValidateFilePath:
    def test_existing_file_returns_a_path(self, tmp_path: Path) -> None:
        f = tmp_path / "data.csv"
        f.write_text("a,b\n")
        result = validate_file_path(str(f))
        assert isinstance(result, Path) and result == f

    def test_missing_file_names_the_path(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="File not found: .*nope.csv"):
            validate_file_path(tmp_path / "nope.csv")

    def test_directory_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Path is not a file"):
            validate_file_path(tmp_path)
