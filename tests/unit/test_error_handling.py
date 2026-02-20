"""Unit tests for exception classes and error-raising paths."""

from __future__ import annotations

import pytest

from mammoth.exceptions import (
    MammothAPIError,
    MammothAuthError,
    MammothColumnError,
    MammothError,
    MammothJobFailedError,
    MammothJobTimeoutError,
    MammothTransformError,
)
from mammoth.models.pipeline import (
    AggregateFunction,
    AggregationSpec,
    ColumnType,
    ConversionSpec,
    CopySpec,
)

# ── Exception class tests ────────────────────────────────────


class TestMammothError:
    def test_base(self):
        err = MammothError("oops")
        assert str(err) == "oops"
        assert err.details == {}

    def test_with_details(self):
        err = MammothError("oops", details={"key": "val"})
        assert err.details == {"key": "val"}


class TestMammothAPIError:
    def test_basic(self):
        err = MammothAPIError("Something went wrong")
        assert str(err) == "Something went wrong"
        assert err.status_code is None
        # Default is empty dict, not None
        assert err.response_body == {}

    def test_with_status_code(self):
        err = MammothAPIError("Not found", status_code=404)
        assert err.status_code == 404

    def test_with_response_body(self):
        body = {"detail": "Resource not found"}
        err = MammothAPIError("Not found", status_code=404, response_body=body)
        assert err.response_body == body


class TestMammothAuthError:
    def test_is_api_error(self):
        err = MammothAuthError("Invalid credentials")
        assert isinstance(err, MammothAPIError)

    def test_message(self):
        err = MammothAuthError("Bad auth")
        assert str(err) == "Bad auth"

    def test_default_message(self):
        err = MammothAuthError()
        assert "Authentication failed" in str(err)
        assert err.status_code == 401


class TestMammothJobTimeoutError:
    def test_message(self):
        err = MammothJobTimeoutError(job_id=42, timeout_seconds=60)
        assert "42" in str(err)
        assert "60" in str(err)
        assert err.details["job_id"] == 42
        assert err.details["timeout"] == 60


class TestMammothJobFailedError:
    def test_without_reason(self):
        err = MammothJobFailedError(job_id=7)
        assert "7" in str(err)
        assert "failed" in str(err)

    def test_with_reason(self):
        err = MammothJobFailedError(job_id=7, failure_reason="bad data")
        assert "bad data" in str(err)
        assert err.details["failure_reason"] == "bad data"


class TestMammothTransformError:
    def test_basic(self):
        err = MammothTransformError("Transform failed")
        assert str(err) == "Transform failed"
        assert err.task_key is None

    def test_with_task_key(self):
        err = MammothTransformError("failed", task_key="PIVOT")
        assert err.task_key == "PIVOT"


class TestMammothColumnError:
    def test_message(self):
        err = MammothColumnError("foo", ["bar", "baz"])
        assert "foo" in str(err)
        assert "not found" in str(err)

    def test_available_columns_in_details(self):
        err = MammothColumnError("foo", ["bar", "baz"])
        assert err.details["column_name"] == "foo"
        assert err.details["available_columns"] == ["bar", "baz"]

    def test_without_available(self):
        err = MammothColumnError("foo")
        assert "foo" in str(err)
        assert "not found" in str(err)


# ── View error paths ─────────────────────────────────────────


class TestResolveColumnErrors:
    def test_unknown_column_raises(self, mock_view):
        with pytest.raises(MammothColumnError, match="nonexistent"):
            mock_view._resolve_column("nonexistent")

    def test_error_lists_available(self, mock_view):
        with pytest.raises(MammothColumnError) as exc_info:
            mock_view._resolve_column("nonexistent")
        assert "emp_id" in str(exc_info.value)

    def test_internal_name_passes_through(self, mock_view):
        result = mock_view._resolve_column("column_abc1234567")
        assert result == "column_abc1234567"


class TestTransformationInputErrors:
    def test_copy_columns_bad_source(self, mock_view):
        with pytest.raises(MammothColumnError, match="no_such_col"):
            mock_view.copy_columns([CopySpec(source="no_such_col", as_name="copy")])

    def test_delete_columns_bad_name(self, mock_view):
        with pytest.raises(MammothColumnError, match="missing_col"):
            mock_view.delete_columns(["missing_col"])

    def test_combine_bad_source(self, mock_view):
        with pytest.raises(MammothColumnError, match="bad_col"):
            mock_view.combine_columns(
                sources=["bad_col", "emp_id"],
                new_column="combined",
            )

    def test_convert_type_bad_column(self, mock_view):
        with pytest.raises(MammothColumnError, match="wrong"):
            mock_view.convert_type([ConversionSpec(column="wrong", to=ColumnType.NUMERIC)])

    def test_math_bad_column(self, mock_view):
        """math() expression parser raises ValueError for unrecognized tokens."""
        with pytest.raises(ValueError, match="Unrecognized token"):
            mock_view.math("bad_col + 1", new_column="result")

    def test_pivot_bad_group_by(self, mock_view):
        with pytest.raises(MammothColumnError, match="nope"):
            mock_view.pivot(
                group_by=["nope"],
                aggregations=[
                    AggregationSpec(
                        column="base_salary", function=AggregateFunction.SUM, as_name="t"
                    )
                ],
            )

    def test_window_bad_partition_by(self, mock_view):
        from mammoth.models.pipeline import WindowFunction

        with pytest.raises(MammothColumnError, match="nope"):
            mock_view.window(
                function=WindowFunction.ROW_NUMBER,
                new_column="rn",
                partition_by=["nope"],
            )
