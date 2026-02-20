"""Pipeline transformation enums and response models.

Provides enums for all transformation parameters used by View methods.
Import commonly-used enums directly from ``mammoth``::

    from mammoth import Operator, ColumnType, JoinType, DateComponent

Enums by category:

    Filtering: Operator, FilterType
    Column types: ColumnType, ValueType
    Joins: JoinType
    Text: TextCase
    Dates: DateComponent, DateDiffUnit
    Aggregation: AggregateFunction
    Windows: WindowFunction, WindowRange
    Fill: FillDirection
    SET values: ProviderType
    Sort: SortDirection
    Math: MathOperator
    Substring: SubstringDirection
    JSON: JsonType
    Tasks: TaskType

Also includes Pydantic models for pipeline task API responses
and the SetValue dataclass for set_values() calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition, NotCondition


class Operator(str, Enum):
    """Filter operators for conditions.

    Use with Condition to build row filters::

        Condition("Sales", Operator.GTE, 1000)
        Condition("Region", Operator.IN_LIST, ["West", "East"])
    """

    IN_LIST = "IN_LIST"
    NOT_IN_LIST = "NOT_IN_LIST"
    GT = "GT"
    LT = "LT"
    GTE = "GTE"
    LTE = "LTE"
    EQ = "EQ"
    NE = "NE"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    NOT_STARTS_WITH = "NOT_STARTS_WITH"
    NOT_ENDS_WITH = "NOT_ENDS_WITH"
    IS_EMPTY = "IS_EMPTY"
    IS_NOT_EMPTY = "IS_NOT_EMPTY"
    IS_MAXVAL = "IS_MAXVAL"
    IS_NOT_MAXVAL = "IS_NOT_MAXVAL"
    IS_MINVAL = "IS_MINVAL"
    IS_NOT_MINVAL = "IS_NOT_MINVAL"


class ColumnType(str, Enum):
    """Column data types for new columns and conversions."""

    TEXT = "TEXT"
    NUMERIC = "NUMERIC"
    DATE = "DATE"


class ValueType(str, Enum):
    """Value types for expressions."""

    FIXED = "FIXED"
    EXPRESSION = "EXPRESSION"
    COLUMN = "COLUMN"
    NUMBER = "NUMBER"
    OPERATOR = "OPERATOR"


class JoinType(str, Enum):
    """Join types for combining dataviews."""

    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    OUTER = "OUTER"


class TextCase(str, Enum):
    """Text case transformations."""

    UPPER = "UPPER"
    LOWER = "LOWER"
    TITLE = "TITLE"


class DateComponent(str, Enum):
    """Date components for extraction.

    Backend uses lowercase values. The enum values are lowercase
    to match the expected COMPONENT payload format.

    Basic components:
        year, month, day, hour, minute, second, week, quarter

    Text-based extractions (return TEXT columns):
        weekday_text, month_text

    Composite date formats (return DATE or TEXT):
        year_month_day_as_date, month_day_year_hour_minute_second
    """

    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"
    WEEK = "week"
    QUARTER = "quarter"
    DAY_OF_WEEK = "day_of_week"
    DAY_OF_YEAR = "day_of_year"
    WEEKDAY_TEXT = "weekday_text"
    MONTH_TEXT = "month_text"
    YEAR_MONTH = "year_month"
    YEAR_WEEK = "year_week"
    YEAR_QUARTER = "year_quarter"
    MONTH_DAY = "month_day"
    HOUR_MINUTE = "hour_minute"
    HOUR_MINUTE_SECOND = "hour_minute_second"
    YEAR_MONTH_DAY = "year_month_day"
    YEAR_MONTH_DAY_AS_DATE = "year_month_day_as_date"
    MONTH_DAY_YEAR_HOUR_MINUTE_SECOND = "month_day_year_hour_minute_second"
    DATE_ONLY = "date_only"


class DateDiffUnit(str, Enum):
    """Date units for date_diff calculations.

    Uses UPPERCASE values (distinct from DateComponent which is lowercase).
    """

    YEAR = "YEAR"
    MONTH = "MONTH"
    DAY = "DAY"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    SECOND = "SECOND"
    WEEK = "WEEK"
    QUARTER = "QUARTER"


class WindowFunction(str, Enum):
    """Window function types."""

    ROW_NUMBER = "ROW_NUMBER"
    RANK = "RANK"
    DENSE_RANK = "DENSE_RANK"
    LAG = "LAG"
    LEAD = "LEAD"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT = "COUNT"
    FIRST_VALUE = "FIRST_VALUE"
    LAST_VALUE = "LAST_VALUE"
    STDDEV = "STDDEV"
    VARIANCE = "VARIANCE"
    PERCENT_RANK = "PERCENT_RANK"
    NTILE = "NTILE"


class WindowRange(str, Enum):
    """Window range types."""

    UNBOUNDED = "UNBOUNDED"
    RUNNING = "RUNNING"


class FillDirection(str, Enum):
    """Fill directions for missing value imputation."""

    FIRST_VALUE = "FIRST_VALUE"
    LAST_VALUE = "LAST_VALUE"


class AggregateFunction(str, Enum):
    """Aggregate functions for pivot/group operations."""

    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    STDDEV = "STDDEV"
    VARIANCE = "VARIANCE"
    MEDIAN = "MEDIAN"
    FIRST = "FIRST"
    LAST = "LAST"
    CONCAT = "CONCAT"


class ProviderType(str, Enum):
    """Value provider types for SET task VALUES items.

    Use in set_values() value specs to control how the value is determined:
        FIXED — a literal value (e.g. "High", 42).
        EXPRESSION — a system expression (e.g. "__TIME__" for current timestamp).
    """

    FIXED = "FIXED"
    EXPRESSION = "EXPRESSION"


class FilterType(str, Enum):
    """Filter types for SELECT (filter_rows) tasks.

    Controls whether matching rows are kept or removed:
        SHOW — keep rows that match the condition.
        REMOVE — discard rows that match the condition.
    """

    SHOW = "SHOW"
    REMOVE = "REMOVE"


class SortDirection(str, Enum):
    """Sort direction for order_by clauses."""

    ASC = "ASC"
    DESC = "DESC"


class MathOperator(str, Enum):
    """Arithmetic operators for math expressions."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"


class SubstringDirection(str, Enum):
    """Extraction direction for substring operations.

    START/END: extract first/last N characters (use with num_char).
    LEFT/RIGHT: extract characters before/after position (use with char_position).
    """

    START = "START"
    END = "END"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class JsonType(str, Enum):
    """JSON structure types for json_extract."""

    OBJECT = "OBJECT"
    LIST = "LIST"


class TaskType(str, Enum):
    """Pipeline task types."""

    SET = "SET"
    SELECT = "SELECT"
    MATH = "MATH"
    JOIN = "JOIN"
    PIVOT = "PIVOT"
    WINDOW = "WINDOW"
    FILL = "FILL"
    LIMIT = "LIMIT"
    LOOKUP = "LOOKUP"
    COMBINE = "COMBINE"
    CONVERT = "CONVERT"
    COPY = "COPY"
    DELETE = "DELETE"
    ADD_COLUMN = "ADD_COLUMN"
    REPLACE = "REPLACE"
    SPLIT = "SPLIT"
    SUBSTRING = "SUBSTRING"
    TEXT_TRANSFORM = "TEXT_TRANSFORM"
    EXTRACT_DATE = "EXTRACT_DATE"
    DATE_DIFF = "DATE_DIFF"
    INCREMENT_DATE = "INCREMENT_DATE"
    UNNEST = "UNNEST"
    CROSSTAB = "CROSSTAB"
    JSON_HANDLE = "JSON_HANDLE"
    GEN_AI = "GEN_AI"
    SQL = "SQL"
    DISCARD_DUPLICATES = "DISCARD_DUPLICATES"


@dataclass
class SetValue:
    """A value specification for set_values().

    Args:
        value: The literal value to set.
        condition: Optional condition — rows matching this condition get this value.

    Example::

        from mammoth import SetValue, Condition, Operator

        values = [
            SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Low"),
        ]
        view.set_values(new_column="Risk", values=values)
    """

    value: Any
    condition: Condition | CompoundCondition | NotCondition | None = field(default=None)


# ── Parameter spec dataclasses ─────────────────────────────────
# These provide IDE autocomplete for dict-based method parameters.
# Each method also accepts plain dicts for backward compatibility.


@dataclass
class CopySpec:
    """Specification for a single column copy in :meth:`View.copy_columns`.

    Example::

        view.copy_columns([CopySpec(source="Sales", as_name="Sales Copy", type="NUMERIC")])
    """

    source: str
    as_name: str | None = None
    type: str = "TEXT"
    condition: Condition | CompoundCondition | NotCondition | None = field(default=None)


@dataclass
class ConversionSpec:
    """Specification for a column type conversion in :meth:`View.convert_type`.

    Example::

        view.convert_type([ConversionSpec(column="Sales", to="NUMERIC")])
        view.convert_type([ConversionSpec(column="Date Col", to="DATE", format="MM/DD/YYYY")])
    """

    column: str
    to: str
    format: str | None = None


@dataclass
class AggregationSpec:
    """Specification for an aggregation in :meth:`View.pivot`.

    Example::

        view.pivot(
            group_by=["Region"],
            aggregations=[AggregationSpec(
                column="Sales", function=AggregateFunction.SUM, as_name="Total",
            )],
        )
    """

    column: str
    function: str | AggregateFunction
    as_name: str | None = None
    delimiter: str | None = None


@dataclass
class JoinKeySpec:
    """Specification for a join key pair in :meth:`View.join`.

    Example::

        view.join(..., on=[JoinKeySpec(left="Customer ID", right="Customer ID")])
    """

    left: str
    right: str


@dataclass
class JoinSelectSpec:
    """Specification for a column to bring in from a join in :meth:`View.join`.

    Example::

        view.join(..., select=[JoinSelectSpec(column="Category", alias="Cat")])
    """

    column: str
    alias: str | None = None


@dataclass
class JsonExtractionSpec:
    """Specification for a JSON key extraction in :meth:`View.json_extract`.

    Example::

        view.json_extract("data", extractions=[
            JsonExtractionSpec(key="name", as_name="Name", type="TEXT"),
            JsonExtractionSpec(key="age", as_name="Age", type="NUMERIC"),
        ])
    """

    key: str
    as_name: str | None = None
    type: str = "TEXT"


@dataclass
class CrosstabSpec:
    """Specification for the aggregation in :meth:`View.crosstab`.

    Example::

        view.crosstab(rows=["Region"], pivot_column="Gender",
                      select=CrosstabSpec(function=AggregateFunction.SUM, column="Sales"))
    """

    function: str | AggregateFunction
    column: str | None = None


# ── Pydantic response models ──────────────────────────────────


class PipelineTaskInfo(BaseModel):
    """Information about a single pipeline task."""

    model_config = {"extra": "allow"}

    id: int | None = None
    dataview_id: int | None = None
    sequence: int | None = None
    task_key: str | None = None
    status: str | None = None
    params: dict[str, Any] | None = None


class PipelineTasksList(BaseModel):
    """List of pipeline tasks."""

    model_config = {"extra": "allow"}

    tasks: list[PipelineTaskInfo] = []
    total: int | None = None


class PipelineInfo(BaseModel):
    """Pipeline state information."""

    model_config = {"extra": "allow"}

    dataview_id: int | None = None
    draft_mode: bool | None = None
    tasks: list[PipelineTaskInfo] = []
