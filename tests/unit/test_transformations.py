"""Unit tests for all transformation methods — verify correct payload structure.

Uses mock_view fixture that captures _add_task payloads.
"""

from __future__ import annotations

import json

from mammoth.condition import Condition
from mammoth.models.pipeline import (
    AggregateFunction,
    ColumnType,
    DateComponent,
    DateDiffUnit,
    FillDirection,
    FilterType,
    JoinType,
    Operator,
    SetValue,
    SortDirection,
    TextCase,
    WindowFunction,
    WindowRange,
)


def last_payload(mock_view):
    """Get the last captured payload."""
    return mock_view._captured_payloads[-1]


# ── Column operations ────────────────────────────────────────


class TestAddColumn:
    def test_basic(self, mock_view):
        mock_view.add_column("New Col")
        p = last_payload(mock_view)
        assert "ADD_COLUMN" in p
        assert p["ADD_COLUMN"][0]["COLUMN"] == "New Col"
        assert p["ADD_COLUMN"][0]["TYPE"] == "TEXT"

    def test_with_enum(self, mock_view):
        mock_view.add_column("Amount", column_type=ColumnType.NUMERIC)
        p = last_payload(mock_view)
        assert p["ADD_COLUMN"][0]["TYPE"] == ColumnType.NUMERIC
        # Verify serializable
        json.dumps(p)

    def test_with_string(self, mock_view):
        mock_view.add_column("Amount", column_type="NUMERIC")
        p = last_payload(mock_view)
        assert p["ADD_COLUMN"][0]["TYPE"] == "NUMERIC"


class TestDeleteColumns:
    def test_basic(self, mock_view):
        mock_view.delete_columns(["gender"])
        p = last_payload(mock_view)
        assert "DELETE" in p
        assert p["DELETE"] == ["column_stu1234567"]

    def test_multiple(self, mock_view):
        mock_view.delete_columns(["gender", "emp_id"])
        p = last_payload(mock_view)
        assert len(p["DELETE"]) == 2


class TestCopyColumns:
    def test_basic(self, mock_view):
        mock_view.copy_columns(
            [
                {"source": "emp_id", "as": "emp_id_copy", "type": "TEXT"},
            ]
        )
        p = last_payload(mock_view)
        assert "COPY" in p
        assert p["VERSION"] == 2
        assert p["COPY"][0]["SOURCE"] == "column_abc1234567"
        assert p["COPY"][0]["AS"]["COLUMN"] == "emp_id_copy"


class TestCombineColumns:
    def test_basic(self, mock_view):
        mock_view.combine_columns(
            sources=["full_name", "department"],
            separator=" - ",
            new_column="combined",
        )
        p = last_payload(mock_view)
        assert "COMBINE" in p
        src = p["COMBINE"]["SOURCE"]
        assert src[0] == {"COLUMN": "column_def1234567"}
        assert src[1] == {"STRING": " - "}
        assert src[2] == {"COLUMN": "column_ghi1234567"}

    def test_three_columns(self, mock_view):
        mock_view.combine_columns(
            sources=["emp_id", "full_name", "department"],
            separator=", ",
            new_column="all",
        )
        p = last_payload(mock_view)
        src = p["COMBINE"]["SOURCE"]
        # 3 cols + 2 separators = 5 items
        assert len(src) == 5


class TestConvertType:
    def test_basic(self, mock_view):
        mock_view.convert_type([{"column": "emp_id", "to": "NUMERIC"}])
        p = last_payload(mock_view)
        assert "CONVERT" in p
        assert p["CONVERT"][0]["SOURCE"] == "column_abc1234567"
        assert p["CONVERT"][0]["TO_TYPE"] == "NUMERIC"


# ── Filter operations ────────────────────────────────────────


class TestFilterRows:
    def test_basic(self, mock_view):
        cond = Condition("department", Operator.EQ, "Engineering")
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        assert p["SELECT"] == "ALL"
        assert "CONDITION" in p
        assert p["CONDITION"]["FILTER_TYPE"] == FilterType.SHOW

    def test_remove(self, mock_view):
        cond = Condition("department", Operator.EQ, "Engineering")
        mock_view.filter_rows(cond, filter_type=FilterType.REMOVE)
        p = last_payload(mock_view)
        assert p["CONDITION"]["FILTER_TYPE"] == FilterType.REMOVE

    def test_string_filter_type(self, mock_view):
        cond = Condition("department", Operator.EQ, "Engineering")
        mock_view.filter_rows(cond, filter_type="SHOW")
        p = last_payload(mock_view)
        assert p["CONDITION"]["FILTER_TYPE"] == "SHOW"


class TestSetValues:
    def test_with_set_value_objects(self, mock_view):
        mock_view.set_values(
            new_column="tier",
            values=[
                SetValue("High", condition=Condition("base_salary", Operator.GTE, 100000)),
                SetValue("Low"),
            ],
        )
        p = last_payload(mock_view)
        assert "SET" in p
        assert p["VERSION"] == 2
        vals = p["SET"]["VALUES"]
        assert vals[0]["PROVIDER"] == "High"
        assert "CONDITION" in vals[0]
        assert vals[1]["PROVIDER"] == "Low"
        assert "CONDITION" not in vals[1]

    def test_with_dicts(self, mock_view):
        mock_view.set_values(
            new_column="status",
            column_type="TEXT",
            values=[
                {"value": "Active"},
            ],
        )
        p = last_payload(mock_view)
        assert p["SET"]["VALUES"][0]["PROVIDER"] == "Active"

    def test_existing_column(self, mock_view):
        mock_view.set_values(
            existing_column="department",
            values=[SetValue("All")],
        )
        p = last_payload(mock_view)
        assert "DESTINATION" in p["SET"]
        assert p["SET"]["DESTINATION"] == "column_ghi1234567"


# ── Math operations ──────────────────────────────────────────


class TestMath:
    def test_string_expression(self, mock_view):
        mock_view.math("base_salary * bonus_pct", new_column="bonus")
        p = last_payload(mock_view)
        assert "MATH" in p
        expr = p["MATH"]["EXPRESSION"]
        assert len(expr) == 3
        assert expr[0] == {"TYPE": "COLUMN", "VALUE": "column_jkl1234567"}
        assert expr[1] == {"TYPE": "OPERATOR", "VALUE": "*"}
        assert expr[2] == {"TYPE": "COLUMN", "VALUE": "column_vwx1234567"}

    def test_raw_list_expression(self, mock_view):
        mock_view.math(
            expression=[
                {"TYPE": "COLUMN", "VALUE": "base_salary"},
                {"TYPE": "OPERATOR", "VALUE": "*"},
                {"TYPE": "NUMBER", "VALUE": 1.1},
            ],
            new_column="raise",
        )
        p = last_payload(mock_view)
        expr = p["MATH"]["EXPRESSION"]
        assert expr[0]["VALUE"] == "column_jkl1234567"
        assert expr[2]["VALUE"] == 1.1


# ── Text operations ──────────────────────────────────────────


class TestTextTransform:
    def test_upper(self, mock_view):
        mock_view.text_transform(["department"], case=TextCase.UPPER)
        p = last_payload(mock_view)
        assert "TEXT_TRANSFORM" in p
        assert p["TEXT_TRANSFORM"]["CASE"] == TextCase.UPPER

    def test_string_case(self, mock_view):
        mock_view.text_transform(["department"], case="UPPER")
        p = last_payload(mock_view)
        assert p["TEXT_TRANSFORM"]["CASE"] == "UPPER"

    def test_trim(self, mock_view):
        mock_view.text_transform(["full_name"], trim=True)
        p = last_payload(mock_view)
        assert p["TEXT_TRANSFORM"]["TRIM"] is True


class TestReplaceValues:
    def test_basic(self, mock_view):
        mock_view.replace_values(columns=["department"], find="Eng", replace="Engineering")
        p = last_payload(mock_view)
        assert "REPLACE" in p
        assert p["REPLACE"]["VALUE_PAIR"][0]["SEARCH_VALUE"] == "Eng"
        assert p["REPLACE"]["VALUE_PAIR"][0]["REPLACE_VALUE"] == "Engineering"


class TestSplitColumn:
    def test_basic(self, mock_view):
        mock_view.split_column(
            column="full_name",
            delimiter=" ",
            new_columns=[
                {"name": "First", "type": "TEXT"},
                {"name": "Last", "type": "TEXT"},
            ],
        )
        p = last_payload(mock_view)
        assert "SPLIT" in p
        assert p["SPLIT"]["SOURCE"] == "column_def1234567"
        assert p["SPLIT"]["DELIMITER"] == " "
        assert len(p["SPLIT"]["AS"]) == 2


class TestSubstring:
    def test_direction_start(self, mock_view):
        mock_view.substring(
            column="full_name",
            direction="START",
            num_char=5,
            new_column="prefix",
        )
        p = last_payload(mock_view)
        assert "SUBSTRING" in p
        assert p["SUBSTRING"]["DIRECTION"] == "START"
        assert p["SUBSTRING"]["NUM_CHAR"] == 5

    def test_regex(self, mock_view):
        mock_view.substring(
            column="full_name",
            regex_pattern="[A-Z]+",
            new_column="caps",
        )
        p = last_payload(mock_view)
        assert p["SUBSTRING"]["REGEX"]["EXPRESSION"] == "[A-Z]+"
        assert p["SUBSTRING"]["REGEX"]["INVERT"] is False


# ── Date operations ──────────────────────────────────────────


class TestExtractDate:
    def test_year(self, mock_view):
        mock_view.extract_date(
            column="joining_date",
            component=DateComponent.YEAR,
            new_column="year",
        )
        p = last_payload(mock_view)
        assert "EXTRACT_DATE" in p
        assert p["EXTRACT_DATE"]["COMPONENT"] == "year"
        assert p["EXTRACT_DATE"]["AS"]["TYPE"] == "NUMERIC"

    def test_string_component(self, mock_view):
        mock_view.extract_date(column="joining_date", component="month", new_column="m")
        p = last_payload(mock_view)
        assert p["EXTRACT_DATE"]["COMPONENT"] == "month"

    def test_text_component(self, mock_view):
        mock_view.extract_date(
            column="joining_date",
            component=DateComponent.WEEKDAY_TEXT,
            new_column="day_name",
        )
        p = last_payload(mock_view)
        assert p["EXTRACT_DATE"]["AS"]["TYPE"] == "TEXT"


class TestDateDiff:
    def test_basic(self, mock_view):
        mock_view.date_diff(
            component=DateDiffUnit.DAY,
            start="joining_date",
            end="exit_date",
            new_column="duration",
        )
        p = last_payload(mock_view)
        assert "DATE_DIFF" in p
        assert p["DATE_DIFF"]["COMPONENT"] == "DAY"
        assert p["DATE_DIFF"]["MINUEND"]["VALUE"] == "column_pqr1234567"
        assert p["DATE_DIFF"]["SUBTRAHEND"]["VALUE"] == "column_mno1234567"

    def test_string_component(self, mock_view):
        mock_view.date_diff(
            component="MONTH",
            start="joining_date",
            end="exit_date",
            new_column="months",
        )
        p = last_payload(mock_view)
        assert p["DATE_DIFF"]["COMPONENT"] == "MONTH"


class TestIncrementDate:
    def test_basic(self, mock_view):
        mock_view.increment_date(
            column="joining_date",
            delta={"DAY": 30},
            new_column="plus_30",
        )
        p = last_payload(mock_view)
        assert "INCREMENT_DATE" in p
        assert p["INCREMENT_DATE"]["DELTA"] == {"DAY": 30}


# ── Row operations ───────────────────────────────────────────


class TestFillMissing:
    def test_basic(self, mock_view):
        mock_view.fill_missing(column="exit_date", direction=FillDirection.LAST_VALUE)
        p = last_payload(mock_view)
        assert "FILL" in p
        assert p["FILL"]["WITH"] == FillDirection.LAST_VALUE

    def test_string_direction(self, mock_view):
        mock_view.fill_missing(column="exit_date", direction="LAST_VALUE")
        p = last_payload(mock_view)
        assert p["FILL"]["WITH"] == "LAST_VALUE"


class TestLimitRows:
    def test_basic(self, mock_view):
        mock_view.limit_rows(n=10)
        p = last_payload(mock_view)
        assert "LIMIT" in p
        assert p["LIMIT"]["LIMIT"] == 10
        assert p["LIMIT"]["BOTTOM"] is False

    def test_with_order(self, mock_view):
        mock_view.limit_rows(n=5, order_by=[["base_salary", "DESC"]])
        p = last_payload(mock_view)
        assert "ORDER_BY" in p


class TestDiscardDuplicates:
    def test_all_columns(self, mock_view):
        mock_view.discard_duplicates()
        p = last_payload(mock_view)
        assert p["DISCARD_DUPLICATES"] is True
        assert p["IGNORE_COLUMNS"] == []

    def test_ignore_columns(self, mock_view):
        mock_view.discard_duplicates(ignore_columns=["emp_id"])
        p = last_payload(mock_view)
        assert p["IGNORE_COLUMNS"] == ["column_abc1234567"]


# ── Aggregation ──────────────────────────────────────────────


class TestPivot:
    def test_basic(self, mock_view):
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                {
                    "column": "base_salary",
                    "function": AggregateFunction.AVG,
                    "as": "avg_salary",
                }
            ],
        )
        p = last_payload(mock_view)
        assert "PIVOT" in p
        assert len(p["PIVOT"]["GROUP_BY"]) == 1
        assert p["PIVOT"]["GROUP_BY"][0]["COLUMN"] == "column_ghi1234567"
        sel = p["PIVOT"]["SELECT"][0]
        assert sel["FUNCTION"] == "AVG"
        assert sel["AS"] == "avg_salary"

    def test_string_function(self, mock_view):
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                {
                    "column": "base_salary",
                    "function": "SUM",
                    "as": "total",
                }
            ],
        )
        p = last_payload(mock_view)
        assert p["PIVOT"]["SELECT"][0]["FUNCTION"] == "SUM"


class TestWindow:
    def test_row_number(self, mock_view):
        mock_view.window(
            function=WindowFunction.ROW_NUMBER,
            new_column="rn",
            partition_by=["department"],
            order_by=[["base_salary", SortDirection.DESC]],
        )
        p = last_payload(mock_view)
        assert "WINDOW" in p
        assert p["WINDOW"]["EVALUATE"]["FUNCTION"] == WindowFunction.ROW_NUMBER
        assert p["WINDOW"]["RANGE"] == WindowRange.UNBOUNDED
        assert len(p["WINDOW"]["GROUP_BY"]) == 1

    def test_string_function(self, mock_view):
        mock_view.window(
            function="SUM",
            column="base_salary",
            new_column="running",
            order_by=[["base_salary", "ASC"]],
        )
        p = last_payload(mock_view)
        assert p["WINDOW"]["EVALUATE"]["FUNCTION"] == "SUM"

    def test_running_range(self, mock_view):
        mock_view.window(
            function=WindowFunction.SUM,
            column="base_salary",
            new_column="running",
            range_type=WindowRange.RUNNING,
        )
        p = last_payload(mock_view)
        assert p["WINDOW"]["RANGE"] == WindowRange.RUNNING


# ── Advanced operations ──────────────────────────────────────


class TestJoin:
    def test_with_int_id(self, mock_view):
        mock_view.join(
            foreign_view=2000,
            join_type=JoinType.LEFT,
            on=[{"left": "emp_id", "right": "column_xxx"}],
            select=[{"column": "column_yyy", "alias": "Category"}],
        )
        p = last_payload(mock_view)
        assert "JOIN" in p
        assert p["JOIN"]["DATAVIEW_ID"] == 2000
        assert p["JOIN"]["TYPE"] == JoinType.LEFT
        assert p["JOIN"]["ON"][0]["LEFT"] == "column_abc1234567"
        assert p["JOIN"]["ON"][0]["RIGHT"] == "column_xxx"

    def test_string_join_type(self, mock_view):
        mock_view.join(
            foreign_view=2000,
            join_type="INNER",
            on=[{"left": "emp_id", "right": "col_x"}],
            select=[{"column": "col_y", "alias": "Y"}],
        )
        p = last_payload(mock_view)
        assert p["JOIN"]["TYPE"] == "INNER"


class TestJsonExtract:
    def test_keys(self, mock_view):
        mock_view.json_extract(
            column="department",
            keys=["name", "code"],
        )
        p = last_payload(mock_view)
        assert "JSON_HANDLE" in p
        extracts = p["JSON_HANDLE"]["JSON_EXTRACT"]
        assert len(extracts) == 2
        assert extracts[0]["KEY"] == "name"
        assert extracts[1]["KEY"] == "code"
        assert p["JSON_HANDLE"]["TYPE"] == "JSON_OBJECT"
        assert p["JSON_HANDLE"]["JSON_OBJECT_OP_TYPE"] == "JSON_OBJECT_TO_COLUMNS"


# ── Payload JSON serialization ───────────────────────────────


class TestPayloadSerialization:
    """Verify all payloads are JSON-serializable (enums serialize correctly)."""

    def test_add_column_serializes(self, mock_view):
        mock_view.add_column("X", ColumnType.NUMERIC)
        json.dumps(last_payload(mock_view))

    def test_filter_serializes(self, mock_view):
        mock_view.filter_rows(
            Condition("department", Operator.EQ, "Eng"),
            filter_type=FilterType.SHOW,
        )
        json.dumps(last_payload(mock_view))

    def test_window_serializes(self, mock_view):
        mock_view.window(
            function=WindowFunction.ROW_NUMBER,
            new_column="rn",
            range_type=WindowRange.UNBOUNDED,
        )
        json.dumps(last_payload(mock_view))

    def test_pivot_serializes(self, mock_view):
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                {
                    "column": "base_salary",
                    "function": AggregateFunction.SUM,
                    "as": "total",
                }
            ],
        )
        json.dumps(last_payload(mock_view))
