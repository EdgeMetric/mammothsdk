"""
Pipeline transformation enums and response models.

Provides enums for operators, column types, join types, and other
transformation parameters, plus Pydantic models for pipeline task responses.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class Operator(str, Enum):
    """Filter operators for conditions.

    Use with Condition to build row filters:
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
    """Date components for extraction and date math."""
    YEAR = "YEAR"
    MONTH = "MONTH"
    DAY = "DAY"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    SECOND = "SECOND"
    WEEK = "WEEK"
    QUARTER = "QUARTER"
    DAY_OF_WEEK = "DAY_OF_WEEK"
    DAY_OF_YEAR = "DAY_OF_YEAR"


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


class PipelineTaskInfo(BaseModel):
    """Information about a single pipeline task."""
    id: Optional[int] = None
    dataview_id: Optional[int] = None
    sequence: Optional[int] = None
    task_key: Optional[str] = None
    status: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class PipelineTasksList(BaseModel):
    """List of pipeline tasks."""
    tasks: List[PipelineTaskInfo] = []
    total: Optional[int] = None

    class Config:
        extra = "allow"


class PipelineInfo(BaseModel):
    """Pipeline state information."""
    dataview_id: Optional[int] = None
    draft_mode: Optional[bool] = None
    tasks: List[PipelineTaskInfo] = []

    class Config:
        extra = "allow"
