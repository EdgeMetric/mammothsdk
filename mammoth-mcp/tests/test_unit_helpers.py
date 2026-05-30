"""Unit tests for mammoth_mcp.helpers — no external dependencies required."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from mammoth_mcp.helpers import (
    _get_recovery_hint,
    build_condition,
    error_response,
    error_result,
    format_view_info,
    handle_errors,
    resolve_enum,
    success_response,
)

# ── success_response ──────────────────────────────────────────


class TestSuccessResponse:
    def test_basic(self):
        r = success_response()
        assert r == {"success": True}

    def test_with_message(self):
        r = success_response(message="done")
        assert r == {"success": True, "message": "done"}

    def test_with_data(self):
        r = success_response(data={"id": 1})
        assert r == {"success": True, "data": {"id": 1}}

    def test_with_data_and_message(self):
        r = success_response(data=[1, 2], message="ok")
        assert r["success"] is True
        assert r["data"] == [1, 2]
        assert r["message"] == "ok"

    def test_data_none_excluded(self):
        r = success_response(data=None, message="hi")
        assert "data" not in r


# ── error_response (dict, backward compat) ────────────────────


class TestErrorResponse:
    def test_basic(self):
        r = error_response(ValueError("bad"))
        assert r["success"] is False
        assert r["error"] == "bad"
        assert r["error_type"] == "ValueError"

    def test_no_hint_for_generic(self):
        r = error_response(RuntimeError("oops"))
        assert "recovery_hint" not in r


# ── error_result (MCP CallToolResult) ─────────────────────────


class TestErrorResult:
    def test_is_error_flag(self):
        from mcp.types import CallToolResult

        result = error_result(ValueError("nope"))
        assert isinstance(result, CallToolResult)
        assert result.isError is True

    def test_content_is_json(self):
        result = error_result(TypeError("wrong type"))
        text = result.content[0].text
        body = json.loads(text)
        assert body["success"] is False
        assert body["error"] == "wrong type"
        assert body["error_type"] == "TypeError"

    def test_recovery_hint_included(self):
        from mammoth.exceptions import MammothColumnError

        result = error_result(MammothColumnError("col not found"))
        body = json.loads(result.content[0].text)
        assert "recovery_hint" in body
        assert "get_view" in body["recovery_hint"]


# ── _get_recovery_hint ────────────────────────────────────────


class TestRecoveryHint:
    def test_column_error(self):
        from mammoth.exceptions import MammothColumnError

        hint = _get_recovery_hint(MammothColumnError("x"))
        assert hint is not None
        assert "column" in hint.lower()

    def test_api_error_401(self):
        from mammoth.exceptions import MammothAPIError

        err = MammothAPIError("auth fail")
        err.status_code = 401
        hint = _get_recovery_hint(err)
        assert hint is not None
        assert "Authentication" in hint

    def test_api_error_500(self):
        from mammoth.exceptions import MammothAPIError

        err = MammothAPIError("internal error")
        err.status_code = 500
        hint = _get_recovery_hint(err)
        assert hint is not None
        assert "Server error" in hint

    def test_timeout(self):
        hint = _get_recovery_hint(TimeoutError("timed out"))
        assert hint is not None
        assert "timed out" in hint.lower()

    def test_generic_no_hint(self):
        hint = _get_recovery_hint(RuntimeError("whatever"))
        assert hint is None


# ── build_condition ───────────────────────────────────────────


class TestBuildCondition:
    def test_simple(self):
        from mammoth import Condition, Operator

        cond = build_condition({"column": "Sales", "operator": "GTE", "value": 100})
        assert isinstance(cond, Condition)
        assert cond.column == "Sales"
        assert cond.operator == Operator.GTE
        assert cond.value == 100

    def test_case_insensitive(self):
        from mammoth import Operator

        cond = build_condition({"column": "X", "operator": "eq", "value": "a"})
        assert cond.operator == Operator.EQ

    def test_no_value(self):
        cond = build_condition({"column": "X", "operator": "IS_EMPTY"})
        assert cond.value is None

    def test_compound_and(self):
        from mammoth import CompoundCondition

        cond = build_condition(
            {
                "logic": "AND",
                "conditions": [
                    {"column": "A", "operator": "EQ", "value": 1},
                    {"column": "B", "operator": "GT", "value": 2},
                ],
            }
        )
        assert isinstance(cond, CompoundCondition)

    def test_compound_or(self):
        from mammoth import CompoundCondition

        cond = build_condition(
            {
                "logic": "OR",
                "conditions": [
                    {"column": "A", "operator": "EQ", "value": 1},
                    {"column": "B", "operator": "EQ", "value": 2},
                ],
            }
        )
        assert isinstance(cond, CompoundCondition)

    def test_invalid_operator(self):
        with pytest.raises(ValueError):
            build_condition({"column": "X", "operator": "INVALID"})


# ── resolve_enum ──────────────────────────────────────────────


class TestResolveEnum:
    def test_by_value(self):
        from mammoth import Operator

        result = resolve_enum(Operator, "GTE")
        assert result == Operator.GTE

    def test_case_insensitive(self):
        from mammoth import Operator

        result = resolve_enum(Operator, "gte")
        assert result == Operator.GTE

    def test_invalid(self):
        from mammoth import Operator

        with pytest.raises(ValueError, match="Invalid value"):
            resolve_enum(Operator, "NOPE")


# ── format_view_info ──────────────────────────────────────────


class TestFormatViewInfo:
    def _make_view(self, row_count=None):
        v = MagicMock()
        v.id = 42
        v.name = "Test View"
        v.dataset_id = 10
        v.display_names = ["Name", "Age"]
        v.columns = {"Name": "col_abc", "Age": "col_def"}
        v.column_types = {"Name": "TEXT", "Age": "NUMERIC"}
        if row_count is not None:
            v.row_count = row_count
        else:
            # Simulate attribute not existing
            del v.row_count
        return v

    def test_basic(self):
        view = self._make_view()
        info = format_view_info(view)
        assert info["id"] == 42
        assert info["name"] == "Test View"
        assert info["dataset_id"] == 10
        assert info["column_count"] == 2
        assert len(info["columns"]) == 2
        assert info["columns"][0]["name"] == "Name"
        assert info["columns"][0]["internal_name"] == "col_abc"
        assert info["columns"][0]["type"] == "TEXT"

    def test_row_count_included(self):
        view = self._make_view(row_count=1500)
        info = format_view_info(view)
        assert info["row_count"] == 1500

    def test_row_count_excluded_when_absent(self):
        view = self._make_view()
        info = format_view_info(view)
        assert "row_count" not in info


# ── handle_errors decorator ───────────────────────────────────


class TestHandleErrors:
    @pytest.mark.asyncio
    async def test_success_passes_through(self):
        @handle_errors
        async def my_tool():
            return {"success": True, "data": "ok"}

        result = await my_tool()
        assert isinstance(result, dict)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_value_error_caught(self):
        from mcp.types import CallToolResult

        @handle_errors
        async def my_tool():
            raise ValueError("bad input")

        result = await my_tool()
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        body = json.loads(result.content[0].text)
        assert body["error"] == "bad input"

    @pytest.mark.asyncio
    async def test_mammoth_api_error_caught(self):
        from mcp.types import CallToolResult

        from mammoth.exceptions import MammothAPIError

        @handle_errors
        async def my_tool():
            raise MammothAPIError("api broke")

        result = await my_tool()
        assert isinstance(result, CallToolResult)
        assert result.isError is True

    @pytest.mark.asyncio
    async def test_unexpected_error_caught(self):
        from mcp.types import CallToolResult

        @handle_errors
        async def my_tool():
            raise OSError("disk full")

        result = await my_tool()
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        body = json.loads(result.content[0].text)
        assert body["error_type"] == "OSError"
