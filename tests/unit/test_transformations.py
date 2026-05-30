"""Unit tests for all transformation methods — verify correct payload structure.

Uses mock_view fixture that captures _add_task payloads.
"""

from __future__ import annotations

import json

from mammoth.condition import Condition
from mammoth.models.pipeline import (
    AggregateFunction,
    AggregationSpec,
    BulkReplaceMapping,
    ColumnType,
    ConversionSpec,
    CopySpec,
    CrosstabSpec,
    DateComponent,
    DateDelta,
    DateDiffUnit,
    FillDirection,
    FilterType,
    JoinKeySpec,
    JoinSelectSpec,
    JoinType,
    JsonExtractionSpec,
    JsonType,
    Operator,
    SetValue,
    SortDirection,
    SplitColumnSpec,
    SubstringDirection,
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
        mock_view.copy_columns([CopySpec(source="emp_id", as_name="emp_id_copy")])
        p = last_payload(mock_view)
        assert "COPY" in p
        assert p["VERSION"] == 2
        assert p["COPY"][0]["SOURCE"] == "column_abc1234567"
        assert p["COPY"][0]["AS"]["COLUMN"] == "emp_id_copy"

    def test_multiple_copies(self, mock_view):
        mock_view.copy_columns(
            [
                CopySpec(source="emp_id", as_name="id_copy"),
                CopySpec(source="base_salary", as_name="salary_copy", type=ColumnType.NUMERIC),
            ]
        )
        p = last_payload(mock_view)
        assert len(p["COPY"]) == 2
        assert p["COPY"][0]["SOURCE"] == "column_abc1234567"
        assert p["COPY"][1]["SOURCE"] == "column_jkl1234567"

    def test_with_condition_per_item(self, mock_view):
        cond = Condition("department", Operator.EQ, "Engineering")
        mock_view.copy_columns(
            [
                CopySpec(source="emp_id", as_name="id_copy", condition=cond),
            ]
        )
        p = last_payload(mock_view)
        assert "CONDITION" in p["COPY"][0]
        assert "column_ghi1234567" in p["COPY"][0]["CONDITION"]


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

    def test_existing_column(self, mock_view):
        mock_view.combine_columns(
            sources=["full_name", "department"],
            separator=" ",
            existing_column="full_name",
        )
        p = last_payload(mock_view)
        assert p["COMBINE"]["DESTINATION"] == "column_def1234567"
        assert "AS" not in p["COMBINE"]

    def test_with_condition(self, mock_view):
        cond = Condition("department", Operator.EQ, "Engineering")
        mock_view.combine_columns(
            sources=["full_name", "department"],
            separator=" - ",
            new_column="combined",
            condition=cond,
        )
        p = last_payload(mock_view)
        assert "CONDITION" in p
        assert "column_ghi1234567" in p["CONDITION"]


class TestConvertType:
    def test_basic(self, mock_view):
        mock_view.convert_type([ConversionSpec(column="emp_id", to=ColumnType.NUMERIC)])
        p = last_payload(mock_view)
        assert "CONVERT" in p
        assert p["CONVERT"][0]["SOURCE"] == "column_abc1234567"
        assert p["CONVERT"][0]["TO_TYPE"] == "NUMERIC"

    def test_multiple_conversions(self, mock_view):
        mock_view.convert_type(
            [
                ConversionSpec(column="emp_id", to=ColumnType.NUMERIC),
                ConversionSpec(column="joining_date", to=ColumnType.DATE),
            ]
        )
        p = last_payload(mock_view)
        assert len(p["CONVERT"]) == 2
        assert p["CONVERT"][1]["TO_TYPE"] == "DATE"

    def test_with_date_format(self, mock_view):
        mock_view.convert_type(
            [
                ConversionSpec(column="joining_date", to=ColumnType.DATE, format="MM/DD/YYYY"),
            ]
        )
        p = last_payload(mock_view)
        assert p["CONVERT"][0]["FORMAT"] == {"date_format": "MM/DD/YYYY"}


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

    def test_compound_and(self, mock_view):
        cond = Condition("department", Operator.EQ, "Eng") & Condition(
            "base_salary", Operator.GTE, 100000
        )
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        assert "AND" in p["CONDITION"]
        assert len(p["CONDITION"]["AND"]) == 2

    def test_compound_or(self, mock_view):
        cond = Condition("department", Operator.EQ, "Eng") | Condition(
            "department", Operator.EQ, "Sales"
        )
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        assert "OR" in p["CONDITION"]
        assert len(p["CONDITION"]["OR"]) == 2

    def test_not(self, mock_view):
        cond = ~Condition("department", Operator.EQ, "Engineering")
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        assert "NOT" in p["CONDITION"]

    def test_nested(self, mock_view):
        cond = (
            Condition("department", Operator.EQ, "Eng")
            & Condition("base_salary", Operator.GTE, 100000)
        ) | Condition("gender", Operator.EQ, "F")
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        assert "OR" in p["CONDITION"]
        assert "AND" in p["CONDITION"]["OR"][0]

    def test_case_insensitive(self, mock_view):
        cond = Condition("department", Operator.EQ, "engineering", case_sensitive=False)
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        assert p["CONDITION"]["STRING_PROP"] == {"CASE": "CASE-INSENSITIVE"}

    def test_with_prompt(self, mock_view):
        cond = Condition("department", Operator.EQ, "Engineering")
        mock_view.filter_rows(cond, prompt="Show only engineering")
        p = last_payload(mock_view)
        assert p["CONDITION"]["PROMPT"] == "Show only engineering"

    def test_value_is_column(self, mock_view):
        cond = Condition("base_salary", Operator.GT, "bonus_pct", value_is_column=True)
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        inner = p["CONDITION"]["column_jkl1234567"]["GT"]
        assert inner == {"COLUMN": "column_vwx1234567"}

    def test_date_component(self, mock_view):
        cond = Condition("joining_date", Operator.EQ, "October", component="month_text")
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        inner = p["CONDITION"]["column_mno1234567"]["EQ"]
        assert inner == {"VALUE": {"COMPONENT": "month_text", "VALUE": "October"}}

    def test_date_truncate(self, mock_view):
        cond = Condition("joining_date", Operator.GT, "2021-02-28", truncate="DAY")
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        inner = p["CONDITION"]["column_mno1234567"]["GT"]
        assert inner == {"VALUE": {"TRUNCATE": "DAY", "VALUE": "2021-02-28"}}


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

    def test_existing_column(self, mock_view):
        mock_view.set_values(
            existing_column="department",
            values=[SetValue("All")],
        )
        p = last_payload(mock_view)
        assert "DESTINATION" in p["SET"]
        assert p["SET"]["DESTINATION"] == "column_ghi1234567"

    def test_multiple_conditional_values(self, mock_view):
        mock_view.set_values(
            new_column="tier",
            values=[
                SetValue("High", condition=Condition("base_salary", Operator.GTE, 100000)),
                SetValue("Medium", condition=Condition("base_salary", Operator.GTE, 50000)),
                SetValue("Low"),
            ],
        )
        p = last_payload(mock_view)
        vals = p["SET"]["VALUES"]
        assert len(vals) == 3
        assert "CONDITION" in vals[0]
        assert "CONDITION" in vals[1]
        assert "CONDITION" not in vals[2]

    def test_compound_condition_in_value(self, mock_view):
        cond = Condition("base_salary", Operator.GTE, 100000) & Condition(
            "department", Operator.EQ, "Eng"
        )
        mock_view.set_values(
            new_column="tier",
            values=[
                SetValue("Top Eng", condition=cond),
                SetValue("Other"),
            ],
        )
        p = last_payload(mock_view)
        vals = p["SET"]["VALUES"]
        assert "AND" in vals[0]["CONDITION"]


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


# ── Text operations ──────────────────────────────────────────


class TestTextTransform:
    def test_upper(self, mock_view):
        mock_view.text_transform(["department"], case=TextCase.UPPER)
        p = last_payload(mock_view)
        assert "TEXT_TRANSFORM" in p
        assert p["TEXT_TRANSFORM"]["CASE"] == TextCase.UPPER

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

    def test_multiple_columns(self, mock_view):
        mock_view.replace_values(columns=["department", "full_name"], find="X", replace="Y")
        p = last_payload(mock_view)
        assert len(p["REPLACE"]["SOURCE"]) == 2

    def test_with_condition(self, mock_view):
        cond = Condition("gender", Operator.EQ, "F")
        mock_view.replace_values(
            columns=["department"], find="Eng", replace="Engineering", condition=cond
        )
        p = last_payload(mock_view)
        assert "CONDITION" in p

    def test_match_options(self, mock_view):
        mock_view.replace_values(
            columns=["department"],
            find="eng",
            replace="Engineering",
            match_case=True,
            match_words=True,
        )
        p = last_payload(mock_view)
        assert p["REPLACE"]["MATCH_CASE"] is True
        assert p["REPLACE"]["MATCH_WORDS"] is True


class TestBulkReplace:
    def test_basic(self, mock_view):
        mock_view.bulk_replace(
            columns=["department"],
            mapping=[BulkReplaceMapping(search=["Eng", "Engineering"], replace="ENGINEERING")],
        )
        p = last_payload(mock_view)
        assert "REPLACE" in p
        assert "MAPPING" in p["REPLACE"]
        assert p["REPLACE"]["MAPPING"][0]["SEARCH_VALUE"] == ["Eng", "Engineering"]
        assert p["REPLACE"]["MAPPING"][0]["REPLACE_VALUE"] == "ENGINEERING"

    def test_with_condition(self, mock_view):
        cond = Condition("gender", Operator.EQ, "M")
        mock_view.bulk_replace(
            columns=["department"],
            mapping=[BulkReplaceMapping(search=["Eng"], replace="Engineering")],
            condition=cond,
        )
        p = last_payload(mock_view)
        assert "CONDITION" in p

    def test_multiple_mappings(self, mock_view):
        mock_view.bulk_replace(
            columns=["department"],
            mapping=[
                BulkReplaceMapping(search=["Eng"], replace="Engineering"),
                BulkReplaceMapping(search=["Mkt"], replace="Marketing"),
            ],
        )
        p = last_payload(mock_view)
        assert len(p["REPLACE"]["MAPPING"]) == 2


class TestSplitColumn:
    def test_basic(self, mock_view):
        mock_view.split_column(
            column="full_name",
            delimiter=" ",
            new_columns=[
                SplitColumnSpec("First"),
                SplitColumnSpec("Last"),
            ],
        )
        p = last_payload(mock_view)
        assert "SPLIT" in p
        assert p["SPLIT"]["SOURCE"] == "column_def1234567"
        assert p["SPLIT"]["DELIMITER"] == " "
        assert len(p["SPLIT"]["AS"]) == 2

    def test_three_columns(self, mock_view):
        mock_view.split_column(
            column="full_name",
            delimiter=" ",
            new_columns=[
                SplitColumnSpec("First"),
                SplitColumnSpec("Middle"),
                SplitColumnSpec("Last"),
            ],
        )
        p = last_payload(mock_view)
        assert len(p["SPLIT"]["AS"]) == 3


class TestSubstring:
    def test_direction_start(self, mock_view):
        mock_view.substring(
            column="full_name",
            direction=SubstringDirection.START,
            num_char=5,
            new_column="prefix",
        )
        p = last_payload(mock_view)
        assert "SUBSTRING" in p
        assert p["SUBSTRING"]["DIRECTION"] == SubstringDirection.START
        assert p["SUBSTRING"]["NUM_CHAR"] == 5

    def test_direction_left(self, mock_view):
        mock_view.substring(
            column="full_name",
            direction=SubstringDirection.LEFT,
            char_position=3,
            new_column="left_chars",
        )
        p = last_payload(mock_view)
        assert p["SUBSTRING"]["DIRECTION"] == SubstringDirection.LEFT
        assert p["SUBSTRING"]["CHAR_POSITION"] == 3

    def test_existing_column(self, mock_view):
        mock_view.substring(
            column="full_name",
            direction=SubstringDirection.START,
            num_char=5,
            existing_column="full_name",
        )
        p = last_payload(mock_view)
        assert p["SUBSTRING"]["DESTINATION"] == "column_def1234567"
        assert "AS" not in p["SUBSTRING"]

    def test_with_condition(self, mock_view):
        cond = Condition("department", Operator.EQ, "Eng")
        mock_view.substring(
            column="full_name",
            direction=SubstringDirection.START,
            num_char=3,
            new_column="prefix",
            condition=cond,
        )
        p = last_payload(mock_view)
        assert "CONDITION" in p

    def test_regex(self, mock_view):
        mock_view.substring(
            column="full_name",
            regex_pattern="[A-Z]+",
            new_column="caps",
        )
        p = last_payload(mock_view)
        assert p["SUBSTRING"]["REGEX"]["EXPRESSION"] == "[A-Z]+"
        assert p["SUBSTRING"]["REGEX"]["INVERT"] is False

    def test_regex_invert(self, mock_view):
        mock_view.substring(
            column="full_name",
            regex_pattern="[0-9]+",
            regex_invert=True,
            new_column="non_digits",
        )
        p = last_payload(mock_view)
        assert p["SUBSTRING"]["REGEX"]["INVERT"] is True


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

    def test_text_component(self, mock_view):
        mock_view.extract_date(
            column="joining_date",
            component=DateComponent.WEEKDAY_TEXT,
            new_column="day_name",
        )
        p = last_payload(mock_view)
        assert p["EXTRACT_DATE"]["AS"]["TYPE"] == "TEXT"

    def test_year_month_day_as_date(self, mock_view):
        mock_view.extract_date(
            column="joining_date",
            component=DateComponent.YEAR_MONTH_DAY_AS_DATE,
            new_column="date_only",
        )
        p = last_payload(mock_view)
        assert p["EXTRACT_DATE"]["AS"]["TYPE"] == "TEXT"

    def test_existing_column(self, mock_view):
        mock_view.extract_date(
            column="joining_date",
            component=DateComponent.YEAR,
            existing_column="exit_date",
        )
        p = last_payload(mock_view)
        assert p["EXTRACT_DATE"]["DESTINATION"] == "column_pqr1234567"
        assert "AS" not in p["EXTRACT_DATE"]

    def test_all_numeric_components(self, mock_view):
        for comp in [
            DateComponent.YEAR,
            DateComponent.MONTH,
            DateComponent.DAY,
            DateComponent.HOUR,
            DateComponent.QUARTER,
            DateComponent.WEEK,
        ]:
            mock_view.extract_date(column="joining_date", component=comp, new_column="x")
            p = last_payload(mock_view)
            assert p["EXTRACT_DATE"]["AS"]["TYPE"] == "NUMERIC"


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

    def test_existing_column(self, mock_view):
        mock_view.date_diff(
            component=DateDiffUnit.DAY,
            start="joining_date",
            end="exit_date",
            existing_column="bonus_pct",
        )
        p = last_payload(mock_view)
        assert p["DATE_DIFF"]["DESTINATION"] == "column_vwx1234567"
        assert "AS" not in p["DATE_DIFF"]


class TestIncrementDate:
    def test_basic(self, mock_view):
        mock_view.increment_date(
            column="joining_date",
            delta=DateDelta(days=30),
            new_column="plus_30",
        )
        p = last_payload(mock_view)
        assert "INCREMENT_DATE" in p
        assert p["INCREMENT_DATE"]["DELTA"] == {"DAY": 30}

    def test_multiple_deltas(self, mock_view):
        mock_view.increment_date(
            column="joining_date",
            delta=DateDelta(years=1, months=-3, days=15),
            new_column="adjusted",
        )
        p = last_payload(mock_view)
        assert p["INCREMENT_DATE"]["DELTA"] == {"YEAR": 1, "MONTH": -3, "DAY": 15}

    def test_negative_deltas(self, mock_view):
        mock_view.increment_date(
            column="joining_date",
            delta=DateDelta(months=-6),
            new_column="six_months_ago",
        )
        p = last_payload(mock_view)
        assert p["INCREMENT_DATE"]["DELTA"]["MONTH"] == -6

    def test_with_condition(self, mock_view):
        cond = Condition("department", Operator.EQ, "Eng")
        mock_view.increment_date(
            column="joining_date",
            delta=DateDelta(days=30),
            new_column="plus_30",
            condition=cond,
        )
        p = last_payload(mock_view)
        assert "CONDITION" in p

    def test_existing_column(self, mock_view):
        mock_view.increment_date(
            column="joining_date",
            delta=DateDelta(days=1),
            existing_column="exit_date",
        )
        p = last_payload(mock_view)
        assert p["INCREMENT_DATE"]["DESTINATION"] == "column_pqr1234567"
        assert "AS" not in p["INCREMENT_DATE"]


# ── Row operations ───────────────────────────────────────────


class TestFillMissing:
    def test_basic(self, mock_view):
        mock_view.fill_missing(column="exit_date", direction=FillDirection.LAST_VALUE)
        p = last_payload(mock_view)
        assert "FILL" in p
        assert p["FILL"]["WITH"] == FillDirection.LAST_VALUE

    def test_with_partition_and_order(self, mock_view):
        mock_view.fill_missing(
            column="exit_date",
            direction=FillDirection.LAST_VALUE,
            partition_by="department",
            order_by=[["joining_date", SortDirection.ASC]],
        )
        p = last_payload(mock_view)
        assert p["FILL"]["PARTITION_BY"] == "column_ghi1234567"
        assert p["FILL"]["ORDER_BY"][0][0] == "column_mno1234567"

    def test_order_by_only(self, mock_view):
        mock_view.fill_missing(
            column="exit_date",
            direction=FillDirection.FIRST_VALUE,
            order_by=[["emp_id", SortDirection.ASC]],
        )
        p = last_payload(mock_view)
        assert "ORDER_BY" in p["FILL"]
        assert "PARTITION_BY" not in p["FILL"]


class TestLimitRows:
    def test_basic(self, mock_view):
        mock_view.limit_rows(n=10)
        p = last_payload(mock_view)
        assert "LIMIT" in p
        assert p["LIMIT"]["LIMIT"] == 10
        assert p["LIMIT"]["BOTTOM"] is False

    def test_with_order(self, mock_view):
        mock_view.limit_rows(n=5, order_by=[["base_salary", SortDirection.DESC]])
        p = last_payload(mock_view)
        assert "ORDER_BY" in p

    def test_bottom_true(self, mock_view):
        mock_view.limit_rows(n=10, bottom=True)
        p = last_payload(mock_view)
        assert p["LIMIT"]["BOTTOM"] is True

    def test_bottom_with_order(self, mock_view):
        mock_view.limit_rows(n=3, bottom=True, order_by=[["base_salary", SortDirection.ASC]])
        p = last_payload(mock_view)
        assert p["LIMIT"]["BOTTOM"] is True
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

    def test_multiple_ignore_columns(self, mock_view):
        mock_view.discard_duplicates(ignore_columns=["emp_id", "gender"])
        p = last_payload(mock_view)
        assert len(p["IGNORE_COLUMNS"]) == 2
        assert "column_abc1234567" in p["IGNORE_COLUMNS"]
        assert "column_stu1234567" in p["IGNORE_COLUMNS"]


class TestUnnest:
    def test_basic(self, mock_view):
        mock_view.unnest(columns=["base_salary", "bonus_pct"])
        p = last_payload(mock_view)
        assert "UNNEST" in p
        assert len(p["UNNEST"]["COLUMNS"]) == 2
        assert p["UNNEST"]["COLUMNS"][0]["COLUMN"] == "column_jkl1234567"
        assert p["UNNEST"]["COLUMNS"][0]["LABEL"] == "base_salary"
        assert p["UNNEST"]["LABEL"]["COLUMN"] == "Label"
        assert p["UNNEST"]["VALUE"]["COLUMN"] == "Value"

    def test_custom_names(self, mock_view):
        mock_view.unnest(
            columns=["base_salary", "bonus_pct"],
            label_column="Metric",
            value_column="Amount",
        )
        p = last_payload(mock_view)
        assert p["UNNEST"]["LABEL"]["COLUMN"] == "Metric"
        assert p["UNNEST"]["VALUE"]["COLUMN"] == "Amount"

    def test_single_column(self, mock_view):
        mock_view.unnest(columns=["base_salary"])
        p = last_payload(mock_view)
        assert len(p["UNNEST"]["COLUMNS"]) == 1


# ── Aggregation ──────────────────────────────────────────────


class TestPivot:
    def test_basic(self, mock_view):
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                AggregationSpec(
                    column="base_salary",
                    function=AggregateFunction.AVG,
                    as_name="avg_salary",
                )
            ],
        )
        p = last_payload(mock_view)
        assert "PIVOT" in p
        assert len(p["PIVOT"]["GROUP_BY"]) == 1
        assert p["PIVOT"]["GROUP_BY"][0]["COLUMN"] == "column_ghi1234567"
        sel = p["PIVOT"]["SELECT"][0]
        assert sel["FUNCTION"] == "AVG"
        assert sel["AS"] == "avg_salary"

    def test_multiple_group_by(self, mock_view):
        mock_view.pivot(
            group_by=["department", "gender"],
            aggregations=[
                AggregationSpec(
                    column="base_salary", function=AggregateFunction.SUM, as_name="total"
                ),
            ],
        )
        p = last_payload(mock_view)
        assert len(p["PIVOT"]["GROUP_BY"]) == 2
        assert p["PIVOT"]["GROUP_BY"][0]["ORDER"] == 0
        assert p["PIVOT"]["GROUP_BY"][1]["ORDER"] == 1

    def test_multiple_aggregations(self, mock_view):
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                AggregationSpec(
                    column="base_salary", function=AggregateFunction.SUM, as_name="total"
                ),
                AggregationSpec(
                    column="base_salary", function=AggregateFunction.AVG, as_name="average"
                ),
            ],
        )
        p = last_payload(mock_view)
        sels = p["PIVOT"]["SELECT"]
        assert len(sels) == 2
        assert sels[0]["FUNCTION"] == "SUM"
        assert sels[1]["FUNCTION"] == "AVG"
        # Orders should be sequential after group_by
        assert sels[0]["ORDER"] == 1
        assert sels[1]["ORDER"] == 2

    def test_with_condition(self, mock_view):
        cond = Condition("gender", Operator.EQ, "F")
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                AggregationSpec(
                    column="base_salary", function=AggregateFunction.AVG, as_name="avg"
                ),
            ],
            condition=cond,
        )
        p = last_payload(mock_view)
        assert "CONDITION" in p["PIVOT"]

    def test_concat_with_delimiter(self, mock_view):
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                AggregationSpec(
                    column="full_name",
                    function=AggregateFunction.CONCAT,
                    as_name="names",
                    delimiter=",",
                ),
            ],
        )
        p = last_payload(mock_view)
        sel = p["PIVOT"]["SELECT"][0]
        assert sel["FUNCTION"] == "CONCAT"
        assert sel["DELIMITER"] == ","


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

    def test_running_range(self, mock_view):
        mock_view.window(
            function=WindowFunction.SUM,
            column="base_salary",
            new_column="running",
            range_type=WindowRange.RUNNING,
        )
        p = last_payload(mock_view)
        assert p["WINDOW"]["RANGE"] == WindowRange.RUNNING

    def test_partition_and_order(self, mock_view):
        mock_view.window(
            function=WindowFunction.SUM,
            column="base_salary",
            new_column="running",
            partition_by=["department", "gender"],
            order_by=[["base_salary", SortDirection.ASC], ["emp_id", SortDirection.DESC]],
        )
        p = last_payload(mock_view)
        assert len(p["WINDOW"]["GROUP_BY"]) == 2
        assert len(p["WINDOW"]["ORDER_BY"]) == 2

    def test_existing_column(self, mock_view):
        mock_view.window(
            function=WindowFunction.RANK,
            existing_column="bonus_pct",
            order_by=[["base_salary", SortDirection.DESC]],
        )
        p = last_payload(mock_view)
        assert p["WINDOW"]["DESTINATION"] == "column_vwx1234567"
        assert "AS" not in p["WINDOW"]

    def test_aggregate_with_sources(self, mock_view):
        mock_view.window(
            function=WindowFunction.SUM,
            column="base_salary",
            new_column="total",
        )
        p = last_payload(mock_view)
        ev = p["WINDOW"]["EVALUATE"]
        assert ev["SOURCES"] == "column_jkl1234567"
        assert ev["ARGUMENTS"] == ["column_jkl1234567"]


class TestCrosstab:
    def test_count_no_column(self, mock_view):
        mock_view.crosstab(
            rows=["department"],
            pivot_column="gender",
            select=CrosstabSpec(function=AggregateFunction.COUNT),
        )
        p = last_payload(mock_view)
        assert "CROSSTAB" in p
        assert p["CROSSTAB"]["SELECT"]["FUNCTION"] == "COUNT"
        assert "COLUMN" not in p["CROSSTAB"]["SELECT"]

    def test_with_column_aggregate(self, mock_view):
        mock_view.crosstab(
            rows=["department"],
            pivot_column="gender",
            select=CrosstabSpec(column="base_salary", function=AggregateFunction.SUM),
        )
        p = last_payload(mock_view)
        assert p["CROSSTAB"]["SELECT"]["FUNCTION"] == "SUM"
        assert p["CROSSTAB"]["SELECT"]["COLUMN"] == "column_jkl1234567"

    def test_multiple_rows(self, mock_view):
        mock_view.crosstab(
            rows=["department", "full_name"],
            pivot_column="gender",
            select=CrosstabSpec(function=AggregateFunction.COUNT),
        )
        p = last_payload(mock_view)
        assert len(p["CROSSTAB"]["ROWS"]) == 2


# ── Advanced operations ──────────────────────────────────────


class TestJoin:
    def test_with_int_id(self, mock_view):
        mock_view.join(
            foreign_view=2000,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="emp_id", right="column_xxx")],
            select=[JoinSelectSpec(column="column_yyy", alias="Category")],
        )
        p = last_payload(mock_view)
        assert "JOIN" in p
        assert p["JOIN"]["DATAVIEW_ID"] == 2000
        assert p["JOIN"]["TYPE"] == JoinType.LEFT
        assert p["JOIN"]["ON"][0]["LEFT"] == "column_abc1234567"
        assert p["JOIN"]["ON"][0]["RIGHT"] == "column_xxx"

    def test_with_view_object(self, mock_view, mock_foreign_view):
        mock_view.join(
            foreign_view=mock_foreign_view,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="emp_id", right="cust_id")],
            select=["category", "region"],
        )
        p = last_payload(mock_view)
        assert p["JOIN"]["DATAVIEW_ID"] == 2050
        assert p["JOIN"]["ON"][0]["LEFT"] == "column_abc1234567"
        assert p["JOIN"]["ON"][0]["RIGHT"] == "column_f_abc12345"
        assert p["JOIN"]["SELECT"][0]["COLUMN"] == "column_f_def12345"
        assert p["JOIN"]["SELECT"][0]["ALIAS"] == "category"
        assert p["JOIN"]["SELECT"][1]["COLUMN"] == "column_f_ghi12345"

    def test_multiple_on_keys(self, mock_view):
        mock_view.join(
            foreign_view=2000,
            join_type=JoinType.INNER,
            on=[
                JoinKeySpec(left="emp_id", right="col_a"),
                JoinKeySpec(left="department", right="col_b"),
            ],
            select=[JoinSelectSpec(column="col_x", alias="X")],
        )
        p = last_payload(mock_view)
        assert len(p["JOIN"]["ON"]) == 2
        assert p["JOIN"]["ON"][1]["LEFT"] == "column_ghi1234567"

    def test_column_prefix(self, mock_view):
        mock_view.join(
            foreign_view=2000,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="emp_id", right="col_x")],
            select=[JoinSelectSpec(column="col_y", alias="Y")],
            column_prefix="fk_",
        )
        p = last_payload(mock_view)
        assert p["JOIN"]["COLUMN_PREFIX"] == "fk_"

    def test_outer_type(self, mock_view):
        mock_view.join(
            foreign_view=2000,
            join_type=JoinType.OUTER,
            on=[JoinKeySpec(left="emp_id", right="col_x")],
            select=[JoinSelectSpec(column="col_y", alias="Y")],
        )
        p = last_payload(mock_view)
        assert p["JOIN"]["TYPE"] == JoinType.OUTER


class TestLookup:
    def test_new_column(self, mock_view):
        mock_view.lookup(
            source="emp_id",
            lookup_view_id=3000,
            key="col_key",
            value="col_val",
            new_column="looked_up",
        )
        p = last_payload(mock_view)
        assert "LOOKUP" in p
        assert p["LOOKUP"]["SOURCE"] == "column_abc1234567"
        assert p["LOOKUP"]["DATAVIEW_ID"] == 3000
        assert p["LOOKUP"]["KEY"] == "col_key"
        assert p["LOOKUP"]["VALUE"] == "col_val"
        assert p["LOOKUP"]["AS"]["COLUMN"] == "looked_up"

    def test_existing_column(self, mock_view):
        mock_view.lookup(
            source="emp_id",
            lookup_view_id=3000,
            key="col_key",
            value="col_val",
            existing_column="department",
        )
        p = last_payload(mock_view)
        assert p["LOOKUP"]["DESTINATION"] == "column_ghi1234567"
        assert "AS" not in p["LOOKUP"]


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

    def test_list_type(self, mock_view):
        mock_view.json_extract(
            column="department",
            json_type=JsonType.LIST,
            keys=["item"],
        )
        p = last_payload(mock_view)
        assert p["JSON_HANDLE"]["TYPE"] == "JSON_LIST"
        assert p["JSON_HANDLE"]["JSON_LIST_OP_TYPE"] == "JSON_LIST_TO_ROWS"

    def test_advanced_extractions(self, mock_view):
        mock_view.json_extract(
            column="department",
            extractions=[
                JsonExtractionSpec(key="name", as_name="Name"),
                JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
            ],
        )
        p = last_payload(mock_view)
        extracts = p["JSON_HANDLE"]["JSON_EXTRACT"]
        assert extracts[0]["COLUMN"] == "Name"
        assert extracts[0]["TYPE"] == "TEXT"
        assert extracts[1]["COLUMN"] == "Age"
        assert extracts[1]["TYPE"] == "NUMERIC"

    def test_keep_source(self, mock_view):
        mock_view.json_extract(
            column="department",
            keys=["name"],
            keep_source=True,
        )
        p = last_payload(mock_view)
        assert p["JSON_HANDLE"]["JSON_KEEP_SOURCE"] is True


class TestGenAI:
    def test_basic(self, mock_view):
        mock_view.gen_ai(
            prompt="Classify sentiment",
            context_columns=["full_name"],
            new_column="Sentiment",
        )
        p = last_payload(mock_view)
        assert "GEN_AI" in p
        assert p["GEN_AI"]["query"] == "Classify sentiment"
        assert p["GEN_AI"]["context_columns"] == ["column_def1234567"]
        assert p["GEN_AI"]["AS"]["COLUMN"] == "Sentiment"

    def test_with_assistant_data(self, mock_view):
        mock_view.gen_ai(
            prompt="Classify",
            context_columns=["full_name"],
            assistant_data=["example1", "example2"],
        )
        p = last_payload(mock_view)
        assert p["GEN_AI"]["ASSISTANT_DATA"] == ["example1", "example2"]

    def test_default_column_name(self, mock_view):
        mock_view.gen_ai(
            prompt="Classify",
            context_columns=["full_name"],
        )
        p = last_payload(mock_view)
        assert p["GEN_AI"]["AS"]["COLUMN"] == "AI Result"

    def test_context_columns_derivation(self, mock_view):
        mock_view.gen_ai(
            prompt="Classify",
            context_columns=["full_name"],
            context_columns_derivation=True,
        )
        p = last_payload(mock_view)
        assert p["GEN_AI"]["context_columns_derivation"] is True

    def test_context_columns_derivation_false(self, mock_view):
        mock_view.gen_ai(
            prompt="Classify",
            context_columns=["full_name"],
            context_columns_derivation=False,
        )
        p = last_payload(mock_view)
        assert p["GEN_AI"]["context_columns_derivation"] is False

    def test_context_columns_derivation_omitted(self, mock_view):
        mock_view.gen_ai(
            prompt="Classify",
            context_columns=["full_name"],
        )
        p = last_payload(mock_view)
        assert "context_columns_derivation" not in p["GEN_AI"]


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
                AggregationSpec(
                    column="base_salary",
                    function=AggregateFunction.SUM,
                    as_name="total",
                )
            ],
        )
        json.dumps(last_payload(mock_view))

    def test_fill_direction_serializes(self, mock_view):
        mock_view.fill_missing(column="exit_date", direction=FillDirection.LAST_VALUE)
        json.dumps(last_payload(mock_view))

    def test_join_type_serializes(self, mock_view):
        mock_view.join(
            foreign_view=2000,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="emp_id", right="col_x")],
            select=[JoinSelectSpec(column="col_y", alias="Y")],
        )
        json.dumps(last_payload(mock_view))

    def test_text_case_serializes(self, mock_view):
        mock_view.text_transform(["department"], case=TextCase.UPPER)
        json.dumps(last_payload(mock_view))

    def test_date_component_serializes(self, mock_view):
        mock_view.extract_date(column="joining_date", component=DateComponent.YEAR, new_column="y")
        json.dumps(last_payload(mock_view))

    def test_date_diff_unit_serializes(self, mock_view):
        mock_view.date_diff(
            component=DateDiffUnit.DAY, start="joining_date", end="exit_date", new_column="d"
        )
        json.dumps(last_payload(mock_view))

    def test_substring_direction_serializes(self, mock_view):
        mock_view.substring(
            column="full_name", direction=SubstringDirection.START, num_char=3, new_column="s"
        )
        json.dumps(last_payload(mock_view))

    def test_sort_direction_serializes(self, mock_view):
        mock_view.limit_rows(n=5, order_by=[["base_salary", SortDirection.DESC]])
        json.dumps(last_payload(mock_view))

    def test_json_type_serializes(self, mock_view):
        mock_view.json_extract(column="department", json_type=JsonType.OBJECT, keys=["k"])
        json.dumps(last_payload(mock_view))

    def test_aggregate_function_serializes(self, mock_view):
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                AggregationSpec(column="base_salary", function=AggregateFunction.COUNT, as_name="c")
            ],
        )
        json.dumps(last_payload(mock_view))


# ── Golden-reference tests ───────────────────────────────────
# Validate exact key names and nesting match backend format.


class TestGoldenReference:
    """Assert payload structures match backend's expected format exactly."""

    def test_golden_set_new_column(self, mock_view):
        mock_view.set_values(
            new_column="status",
            values=[SetValue("Active")],
        )
        p = last_payload(mock_view)
        assert isinstance(p["SET"], dict), "SET must be a dict, not a list"
        assert "AS" in p["SET"]
        assert p["SET"]["AS"]["COLUMN"] == "status"
        assert p["SET"]["AS"]["TYPE"] == "TEXT"
        assert isinstance(p["SET"]["VALUES"], list)
        assert p["SET"]["VALUES"][0]["PROVIDER_TYPE"] == "FIXED"
        assert p["SET"]["VALUES"][0]["PROVIDER"] == "Active"
        assert p["VERSION"] == 2

    def test_golden_set_existing_column(self, mock_view):
        mock_view.set_values(
            existing_column="department",
            values=[SetValue("All")],
        )
        p = last_payload(mock_view)
        assert isinstance(p["SET"], dict)
        assert "DESTINATION" in p["SET"]
        assert p["SET"]["DESTINATION"] == "column_ghi1234567"
        assert "AS" not in p["SET"]
        assert p["VERSION"] == 2

    def test_golden_set_conditional(self, mock_view):
        mock_view.set_values(
            new_column="tier",
            values=[
                SetValue("High", condition=Condition("base_salary", Operator.GTE, 100000)),
                SetValue("Low"),
            ],
        )
        p = last_payload(mock_view)
        vals = p["SET"]["VALUES"]
        assert "CONDITION" in vals[0]
        assert vals[0]["PROVIDER_TYPE"] == "FIXED"
        assert vals[1]["PROVIDER"] == "Low"
        assert "CONDITION" not in vals[1]

    def test_golden_select(self, mock_view):
        cond = Condition("department", Operator.EQ, "Eng")
        mock_view.filter_rows(cond, prompt="Show engineering")
        p = last_payload(mock_view)
        assert p["SELECT"] == "ALL"
        assert "CONDITION" in p
        assert p["CONDITION"]["FILTER_TYPE"] == FilterType.SHOW
        assert p["CONDITION"]["PROMPT"] == "Show engineering"

    def test_golden_fill(self, mock_view):
        mock_view.fill_missing(
            column="exit_date",
            direction=FillDirection.LAST_VALUE,
            partition_by="department",
            order_by=[["joining_date", SortDirection.ASC]],
        )
        p = last_payload(mock_view)
        fill = p["FILL"]
        assert fill["COLUMN"] == "column_pqr1234567"
        assert fill["WITH"] == "LAST_VALUE"
        assert fill["PARTITION_BY"] == "column_ghi1234567"
        assert fill["ORDER_BY"] == [["column_mno1234567", "ASC"]]

    def test_golden_replace(self, mock_view):
        mock_view.replace_values(
            columns=["department"],
            find="Eng",
            replace="Engineering",
            match_case=True,
            match_words=False,
        )
        p = last_payload(mock_view)
        r = p["REPLACE"]
        assert r["SOURCE"] == ["column_ghi1234567"]
        assert r["VALUE_PAIR"][0]["SEARCH_VALUE"] == "Eng"
        assert r["VALUE_PAIR"][0]["REPLACE_VALUE"] == "Engineering"
        assert r["MATCH_CASE"] is True
        assert r["MATCH_WORDS"] is False

    def test_golden_bulk_replace(self, mock_view):
        mock_view.bulk_replace(
            columns=["department"],
            mapping=[BulkReplaceMapping(search=["Eng", "Engineering"], replace="ENGINEERING")],
        )
        p = last_payload(mock_view)
        m = p["REPLACE"]["MAPPING"][0]
        assert isinstance(m["SEARCH_VALUE"], list)
        assert m["REPLACE_VALUE"] == "ENGINEERING"

    def test_golden_increment_date(self, mock_view):
        mock_view.increment_date(
            column="joining_date",
            delta=DateDelta(years=1, months=-3),
            new_column="adjusted",
        )
        p = last_payload(mock_view)
        inc = p["INCREMENT_DATE"]
        assert inc["SOURCE"] == "column_mno1234567"
        assert inc["DELTA"] == {"YEAR": 1, "MONTH": -3}
        assert "AS" in inc
        assert inc["AS"]["COLUMN"] == "adjusted"

    def test_golden_extract_date(self, mock_view):
        mock_view.extract_date(
            column="joining_date",
            component=DateComponent.YEAR,
            new_column="year",
        )
        p = last_payload(mock_view)
        ed = p["EXTRACT_DATE"]
        assert ed["COMPONENT"] == "year"  # lowercase
        assert ed["SOURCE"] == "column_mno1234567"
        assert ed["AS"]["TYPE"] == "NUMERIC"

    def test_golden_date_diff(self, mock_view):
        mock_view.date_diff(
            component=DateDiffUnit.MONTH,
            start="joining_date",
            end="exit_date",
            new_column="months",
        )
        p = last_payload(mock_view)
        dd = p["DATE_DIFF"]
        assert dd["COMPONENT"] == "MONTH"
        assert dd["MINUEND"]["TYPE"] == "COLUMN"
        assert dd["SUBTRAHEND"]["TYPE"] == "COLUMN"
        assert "AS" in dd

    def test_golden_math(self, mock_view):
        mock_view.math("base_salary * bonus_pct", new_column="bonus")
        p = last_payload(mock_view)
        m = p["MATH"]
        assert isinstance(m["EXPRESSION"], list)
        assert m["EXPRESSION"][0]["TYPE"] == "COLUMN"
        assert m["EXPRESSION"][1]["TYPE"] == "OPERATOR"
        assert m["EXPRESSION"][1]["VALUE"] == "*"
        assert "AS" in m

    def test_golden_window(self, mock_view):
        mock_view.window(
            function=WindowFunction.SUM,
            column="base_salary",
            new_column="running",
            partition_by=["department"],
            order_by=[["base_salary", SortDirection.ASC]],
        )
        p = last_payload(mock_view)
        w = p["WINDOW"]
        ev = w["EVALUATE"]
        assert ev["FUNCTION"] == "SUM"
        assert ev["SOURCES"] == "column_jkl1234567"
        assert ev["ARGUMENTS"] == ["column_jkl1234567"]
        assert w["GROUP_BY"][0]["COLUMN"] == "column_ghi1234567"
        assert w["ORDER_BY"] == [["column_jkl1234567", "ASC"]]
        assert "AS" in w

    def test_golden_text_transform(self, mock_view):
        mock_view.text_transform(["department"], case=TextCase.UPPER, trim=True)
        p = last_payload(mock_view)
        tt = p["TEXT_TRANSFORM"]
        assert tt["SOURCE"] == ["column_ghi1234567"]
        assert tt["TRIM"] is True
        assert tt["CASE"] == "UPPER"

    def test_golden_pivot(self, mock_view):
        mock_view.pivot(
            group_by=["department"],
            aggregations=[
                AggregationSpec(
                    column="base_salary", function=AggregateFunction.SUM, as_name="total"
                ),
            ],
        )
        p = last_payload(mock_view)
        pv = p["PIVOT"]
        assert pv["GROUP_BY"][0]["COLUMN"] == "column_ghi1234567"
        assert pv["GROUP_BY"][0]["ORDER"] == 0
        assert pv["SELECT"][0]["FUNCTION"] == "SUM"
        assert pv["SELECT"][0]["COLUMN"] == "column_jkl1234567"
        assert pv["SELECT"][0]["AS"] == "total"

    def test_golden_add_column(self, mock_view):
        mock_view.add_column("Notes", column_type=ColumnType.TEXT)
        p = last_payload(mock_view)
        col = p["ADD_COLUMN"][0]
        assert col["COLUMN"] == "Notes"
        assert col["TYPE"] == "TEXT"
        assert "INTERNAL_NAME" in col

    def test_golden_copy(self, mock_view):
        mock_view.copy_columns(
            [
                CopySpec(source="emp_id", as_name="emp_copy"),
            ]
        )
        p = last_payload(mock_view)
        assert p["VERSION"] == 2
        assert p["COPY"][0]["SOURCE"] == "column_abc1234567"
        assert p["COPY"][0]["AS"]["COLUMN"] == "emp_copy"

    def test_golden_combine(self, mock_view):
        mock_view.combine_columns(
            sources=["full_name", "department"],
            separator=" - ",
            new_column="combined",
        )
        p = last_payload(mock_view)
        src = p["COMBINE"]["SOURCE"]
        assert src[0] == {"COLUMN": "column_def1234567"}
        assert src[1] == {"STRING": " - "}
        assert src[2] == {"COLUMN": "column_ghi1234567"}
        assert "AS" in p["COMBINE"]

    def test_golden_convert(self, mock_view):
        mock_view.convert_type([ConversionSpec(column="emp_id", to=ColumnType.NUMERIC)])
        p = last_payload(mock_view)
        assert p["CONVERT"][0]["SOURCE"] == "column_abc1234567"
        assert p["CONVERT"][0]["TO_TYPE"] == "NUMERIC"

    def test_golden_delete(self, mock_view):
        mock_view.delete_columns(["gender", "bonus_pct"])
        p = last_payload(mock_view)
        assert isinstance(p["DELETE"], list)
        assert "column_stu1234567" in p["DELETE"]
        assert "column_vwx1234567" in p["DELETE"]

    def test_golden_split(self, mock_view):
        mock_view.split_column(
            column="full_name",
            delimiter=" ",
            new_columns=[
                SplitColumnSpec("First"),
                SplitColumnSpec("Last"),
            ],
        )
        p = last_payload(mock_view)
        s = p["SPLIT"]
        assert s["SOURCE"] == "column_def1234567"
        assert s["DELIMITER"] == " "
        assert len(s["AS"]) == 2
        assert s["AS"][0]["COLUMN"] == "First"

    def test_golden_substring_regex(self, mock_view):
        mock_view.substring(
            column="full_name",
            regex_pattern="[A-Z]+",
            regex_invert=True,
            new_column="caps",
        )
        p = last_payload(mock_view)
        ss = p["SUBSTRING"]
        assert ss["REGEX"]["EXPRESSION"] == "[A-Z]+"
        assert ss["REGEX"]["INVERT"] is True
        assert "AS" in ss

    def test_golden_json_object(self, mock_view):
        mock_view.json_extract(
            column="department",
            json_type=JsonType.OBJECT,
            keys=["name"],
        )
        p = last_payload(mock_view)
        jh = p["JSON_HANDLE"]
        assert jh["TYPE"] == "JSON_OBJECT"
        assert jh["JSON_OBJECT_OP_TYPE"] == "JSON_OBJECT_TO_COLUMNS"
        assert jh["JSON_EXTRACT"][0]["KEY"] == "name"

    def test_golden_json_list(self, mock_view):
        mock_view.json_extract(
            column="department",
            json_type=JsonType.LIST,
            keys=["item"],
        )
        p = last_payload(mock_view)
        jh = p["JSON_HANDLE"]
        assert jh["TYPE"] == "JSON_LIST"
        assert jh["JSON_LIST_OP_TYPE"] == "JSON_LIST_TO_ROWS"

    def test_golden_join(self, mock_view, mock_foreign_view):
        mock_view.join(
            foreign_view=mock_foreign_view,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="emp_id", right="cust_id")],
            select=["category"],
        )
        p = last_payload(mock_view)
        j = p["JOIN"]
        assert "JOIN_ID" in j
        assert j["DATAVIEW_ID"] == 2050
        assert j["TYPE"] == "LEFT"
        assert j["ON"][0]["LEFT"] == "column_abc1234567"
        assert j["ON"][0]["RIGHT"] == "column_f_abc12345"
        assert j["SELECT"][0]["COLUMN"] == "column_f_def12345"
        assert j["SELECT"][0]["ALIAS"] == "category"

    def test_golden_lookup(self, mock_view):
        mock_view.lookup(
            source="emp_id",
            lookup_view_id=3000,
            key="col_key",
            value="col_val",
            new_column="looked_up",
        )
        p = last_payload(mock_view)
        lk = p["LOOKUP"]
        assert lk["SOURCE"] == "column_abc1234567"
        assert lk["DATAVIEW_ID"] == 3000
        assert lk["KEY"] == "col_key"
        assert lk["VALUE"] == "col_val"
        assert lk["AS"]["COLUMN"] == "looked_up"

    def test_golden_unnest(self, mock_view):
        mock_view.unnest(columns=["base_salary", "bonus_pct"])
        p = last_payload(mock_view)
        u = p["UNNEST"]
        assert u["COLUMNS"][0]["COLUMN"] == "column_jkl1234567"
        assert u["COLUMNS"][0]["LABEL"] == "base_salary"
        assert u["LABEL"]["COLUMN"] == "Label"
        assert u["LABEL"]["TYPE"] == "TEXT"
        assert u["VALUE"]["COLUMN"] == "Value"

    def test_golden_discard_duplicates(self, mock_view):
        mock_view.discard_duplicates(ignore_columns=["emp_id"])
        p = last_payload(mock_view)
        assert p["DISCARD_DUPLICATES"] is True
        assert p["IGNORE_COLUMNS"] == ["column_abc1234567"]

    def test_golden_limit(self, mock_view):
        mock_view.limit_rows(n=10, bottom=True, order_by=[["base_salary", SortDirection.DESC]])
        p = last_payload(mock_view)
        assert p["LIMIT"]["LIMIT"] == 10
        assert p["LIMIT"]["BOTTOM"] is True
        assert "ORDER_BY" in p

    def test_golden_gen_ai(self, mock_view):
        mock_view.gen_ai(
            prompt="Classify sentiment",
            context_columns=["full_name"],
            new_column="Sentiment",
        )
        p = last_payload(mock_view)
        ga = p["GEN_AI"]
        assert ga["query"] == "Classify sentiment"  # lowercase key
        assert ga["context_columns"] == ["column_def1234567"]  # lowercase key
        assert ga["AS"]["COLUMN"] == "Sentiment"
        assert isinstance(ga["ASSISTANT_DATA"], list)

    def test_golden_crosstab(self, mock_view):
        mock_view.crosstab(
            rows=["department"],
            pivot_column="gender",
            select=CrosstabSpec(column="base_salary", function=AggregateFunction.SUM),
        )
        p = last_payload(mock_view)
        ct = p["CROSSTAB"]
        assert isinstance(ct["ROWS"], list)
        assert isinstance(ct["COLUMNS"], list)
        assert ct["SELECT"]["FUNCTION"] == "SUM"
        assert ct["SELECT"]["COLUMN"] == "column_jkl1234567"

    def test_golden_text_eq_remaps_to_in_list(self, mock_view):
        """TEXT column + EQ condition emits IN_LIST (backend workaround)."""
        cond = Condition("department", Operator.EQ, "Engineering")
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        inner = p["CONDITION"]["column_ghi1234567"]
        assert "IN_LIST" in inner, "TEXT + EQ should be remapped to IN_LIST"
        assert inner["IN_LIST"]["VALUE"] == ["Engineering"]

    def test_golden_text_ne_remaps_to_not_in_list(self, mock_view):
        """TEXT column + NE condition emits NOT_IN_LIST (backend workaround)."""
        cond = Condition("gender", Operator.NE, "M")
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        inner = p["CONDITION"]["column_stu1234567"]
        assert "NOT_IN_LIST" in inner, "TEXT + NE should be remapped to NOT_IN_LIST"
        assert inner["NOT_IN_LIST"]["VALUE"] == ["M"]

    def test_golden_set_with_text_eq_condition(self, mock_view):
        """SET VALUES with TEXT EQ condition uses IN_LIST workaround."""
        mock_view.set_values(
            new_column="label",
            values=[
                SetValue("Eng", condition=Condition("department", Operator.EQ, "Engineering")),
                SetValue("Other"),
            ],
        )
        p = last_payload(mock_view)
        cond = p["SET"]["VALUES"][0]["CONDITION"]
        assert "IN_LIST" in cond["column_ghi1234567"]
        assert cond["column_ghi1234567"]["IN_LIST"]["VALUE"] == ["Engineering"]

    def test_golden_numeric_eq_unchanged(self, mock_view):
        """NUMERIC column + EQ stays EQ (remap only for TEXT)."""
        cond = Condition("base_salary", Operator.EQ, 50000)
        mock_view.filter_rows(cond)
        p = last_payload(mock_view)
        inner = p["CONDITION"]["column_jkl1234567"]
        assert "EQ" in inner
        assert inner["EQ"]["VALUE"] == 50000


# ── Param templates unit tests ───────────────────────────────


class TestParamTemplates:
    """Test standalone _param_templates builders directly."""

    def test_set_params_structure(self):
        from mammoth._param_templates import set_params

        result = set_params(
            set_values={
                "AS": {"COLUMN": "Status", "TYPE": "TEXT"},
                "VALUES": [{"PROVIDER_TYPE": "FIXED", "PROVIDER": "Active"}],
            },
            version=2,
        )
        assert isinstance(result["SET"], dict), "SET must be a dict, not a list"
        assert result["SET"]["AS"]["COLUMN"] == "Status"
        assert result["VERSION"] == 2

    def test_set_params_no_list_wrap(self):
        """Ensure a dict input stays as a dict, not wrapped in a list."""
        from mammoth._param_templates import set_params

        single = {"AS": {"COLUMN": "X", "TYPE": "TEXT"}, "VALUES": []}
        result = set_params(set_values=single, version=2)
        assert result["SET"] is single

    def test_copy_params_has_version(self):
        from mammoth._param_templates import copy_params

        result = copy_params([{"SOURCE": "col_1", "AS": {"COLUMN": "Copy", "TYPE": "TEXT"}}])
        assert result["VERSION"] == 2
        assert result["COPY"][0]["SOURCE"] == "col_1"

    def test_all_templates_json_serializable(self):
        from mammoth import _param_templates as pt

        payloads = [
            pt.add_column_params([{"COLUMN": "X", "TYPE": "TEXT"}]),
            pt.combine_params(
                [{"COLUMN": "c1"}, {"STRING": " "}, {"COLUMN": "c2"}],
                as_column={"COLUMN": "C", "TYPE": "TEXT"},
            ),
            pt.convert_params([{"SOURCE": "c1", "TO_TYPE": "NUMERIC"}]),
            pt.copy_params([{"SOURCE": "c1", "AS": {"COLUMN": "C", "TYPE": "TEXT"}}]),
            pt.crosstab_params([{"COLUMN": "c1"}], [{"COLUMN": "c2"}], {"FUNCTION": "COUNT"}),
            pt.date_diff_params(
                "DAY",
                {"TYPE": "COLUMN", "VALUE": "c1"},
                {"TYPE": "COLUMN", "VALUE": "c2"},
                as_column={"COLUMN": "D", "TYPE": "NUMERIC"},
            ),
            pt.delete_params(["c1"]),
            pt.extract_date_params("c1", "year", as_column={"COLUMN": "Y", "TYPE": "NUMERIC"}),
            pt.fill_params("c1", "LAST_VALUE"),
            pt.gen_ai_params({"COLUMN": "AI", "TYPE": "TEXT"}, ["data"], "prompt", ["c1"]),
            pt.increment_date_params("c1", {"DAY": 1}, as_column={"COLUMN": "D", "TYPE": "DATE"}),
            pt.join_params(
                "j1", 100, "LEFT", [{"LEFT": "c1", "RIGHT": "c2"}], [{"COLUMN": "c3", "ALIAS": "A"}]
            ),
            pt.json_handle_params(
                "c1", "JSON_OBJECT", [{"KEY": "k"}], json_object_op_type="JSON_OBJECT_TO_COLUMNS"
            ),
            pt.limit_params(10),
            pt.lookup_params(
                "c1",
                as_column={"COLUMN": "L", "TYPE": "TEXT"},
                lookup_dataview_id=200,
                key="k",
                value="v",
            ),
            pt.math_params(
                [
                    {"TYPE": "COLUMN", "VALUE": "c1"},
                    {"TYPE": "OPERATOR", "VALUE": "+"},
                    {"TYPE": "NUMBER", "VALUE": 1},
                ],
                as_column={"COLUMN": "M", "TYPE": "NUMERIC"},
            ),
            pt.pivot_params(
                [{"COLUMN": "c1", "ORDER": 0}],
                [{"FUNCTION": "SUM", "COLUMN": "c2", "AS": "T", "ORDER": 1}],
            ),
            pt.replace_params(["c1"], value_pairs=[{"SEARCH_VALUE": "a", "REPLACE_VALUE": "b"}]),
            pt.select_params("ALL", condition={"c1": {"EQ": {"VALUE": 1}}, "FILTER_TYPE": "SHOW"}),
            pt.set_params({"AS": {"COLUMN": "S", "TYPE": "TEXT"}, "VALUES": []}, version=2),
            pt.split_params("c1", ",", [{"COLUMN": "A", "TYPE": "TEXT"}]),
            pt.substring_params(
                "c1",
                regex={"EXPRESSION": ".*", "INVERT": False},
                as_column={"COLUMN": "S", "TYPE": "TEXT"},
            ),
            pt.text_transform_params(["c1"], trim=True, case="UPPER"),
            pt.unnest_params(
                [{"COLUMN": "c1", "LABEL": "L"}],
                {"COLUMN": "Label", "TYPE": "TEXT"},
                {"COLUMN": "Value", "TYPE": "TEXT"},
            ),
            pt.window_params(
                {"FUNCTION": "SUM", "SOURCES": "c1", "ARGUMENTS": ["c1"]},
                as_column={"COLUMN": "W", "TYPE": "NUMERIC"},
            ),
            pt.discard_duplicates_params(ignore_columns=["c1"]),
        ]
        for payload in payloads:
            json.dumps(payload)  # must not raise
