"""Mammoth Analytics Python SDK.

A Python client for the Mammoth Analytics platform API. Provides
resource-based CRUD, rich View objects with 25+ transformation methods,
a condition builder with operator overloading, and export helpers.

Quick start::

    from mammoth import MammothClient, Condition, Operator, ColumnType, SetValue

    client = MammothClient(
        api_key="your-api-key",
        api_secret="your-api-secret",
        workspace_id=11,
    )
    client.set_project_id(10)

    # Resource-based CRUD
    projects = client.projects.list()
    datasets = client.datasets.list()

    # Rich View objects with transformations
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.set_values(
        new_column="Category",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Low"),
        ],
    )
    view.export.to_csv("output.csv")

Key modules:
    - ``mammoth.client``: MammothClient — main entry point.
    - ``mammoth.view``: View, ViewExport — data transformations and exports.
    - ``mammoth.condition``: Condition, CompoundCondition — filter builder.
    - ``mammoth.models.pipeline``: Enums (Operator, ColumnType, JoinType, etc.).
"""

from __future__ import annotations

from mammoth.client import (
    DEFAULT_JOB_TIMEOUT,
    DEFAULT_PIPELINE_TIMEOUT,
    DEFAULT_TIMEOUT,
    MammothClient,
)
from mammoth.condition import CompoundCondition, Condition, NotCondition
from mammoth.exceptions import (
    MammothAPIError,
    MammothAuthError,
    MammothColumnError,
    MammothError,
    MammothJobFailedError,
    MammothJobTimeoutError,
    MammothTransformError,
)
from mammoth.helpers import parse_path
from mammoth.models.exports import HandlerType, TriggerType
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
    DraftCommand,
    ExportFileType,
    FillDirection,
    FilterType,
    JoinKeySpec,
    JoinSelectSpec,
    JoinType,
    JsonExtractionSpec,
    JsonOpType,
    JsonType,
    MathOperator,
    Operator,
    ProviderType,
    SetValue,
    SortDirection,
    SplitColumnSpec,
    SubstringDirection,
    TaskType,
    TextCase,
    ValueType,
    WindowFunction,
    WindowRange,
)
from mammoth.models.webhooks import WebhookMode
from mammoth.view import View, ViewExport

__version__ = "0.3.7"
__all__ = [
    # Client
    "MammothClient",
    "DEFAULT_TIMEOUT",
    "DEFAULT_JOB_TIMEOUT",
    "DEFAULT_PIPELINE_TIMEOUT",
    # Condition builder
    "Condition",
    "CompoundCondition",
    "NotCondition",
    # View
    "View",
    "ViewExport",
    # Enums
    "Operator",
    "ColumnType",
    "JoinType",
    "TextCase",
    "DateComponent",
    "DateDiffUnit",
    "WindowFunction",
    "WindowRange",
    "FillDirection",
    "AggregateFunction",
    "FilterType",
    "SortDirection",
    "SubstringDirection",
    "JsonType",
    "JsonOpType",
    "ExportFileType",
    "MathOperator",
    "ProviderType",
    "TaskType",
    "DraftCommand",
    "ValueType",
    # Parameter spec dataclasses
    "SetValue",
    "CopySpec",
    "ConversionSpec",
    "AggregationSpec",
    "JoinKeySpec",
    "JoinSelectSpec",
    "JsonExtractionSpec",
    "CrosstabSpec",
    "SplitColumnSpec",
    "BulkReplaceMapping",
    "DateDelta",
    # Export enums
    "HandlerType",
    "TriggerType",
    # Exceptions
    "MammothError",
    "MammothAPIError",
    "MammothAuthError",
    "MammothTransformError",
    "MammothColumnError",
    "MammothJobTimeoutError",
    "MammothJobFailedError",
    # Webhooks
    "WebhookMode",
    # Helpers
    "parse_path",
]
