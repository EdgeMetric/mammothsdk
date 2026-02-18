"""
Mammoth Analytics Python SDK

A Python client for the Mammoth Analytics platform API.

Quick start:
    from mammoth import MammothClient, Condition, Operator

    client = MammothClient(api_key="...", api_secret="...", workspace_id=4)
    client.set_project_id(10)

    # Resource-based CRUD
    projects = client.projects.list()
    datasets = client.datasets.list()

    # Rich View objects with transformations
    view = client.views.get(1039)
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.export.to_csv("output.csv")
"""

from .client import MammothClient
from .condition import Condition, CompoundCondition
from .view import View, ViewExport
from .models.pipeline import (
    Operator,
    ColumnType,
    ValueType,
    JoinType,
    TextCase,
    DateComponent,
    WindowFunction,
    FillDirection,
    AggregateFunction,
)
from .exceptions import (
    MammothError,
    MammothAPIError,
    MammothAuthError,
    MammothTransformError,
    MammothColumnError,
    MammothJobTimeoutError,
    MammothJobFailedError,
)
from .helpers import parse_path
from .models import *

__version__ = "0.1.0"
__all__ = [
    # Client
    "MammothClient",
    # Condition builder
    "Condition",
    "CompoundCondition",
    # View
    "View",
    "ViewExport",
    # Enums
    "Operator",
    "ColumnType",
    "ValueType",
    "JoinType",
    "TextCase",
    "DateComponent",
    "WindowFunction",
    "FillDirection",
    "AggregateFunction",
    # Exceptions
    "MammothError",
    "MammothAPIError",
    "MammothAuthError",
    "MammothTransformError",
    "MammothColumnError",
    "MammothJobTimeoutError",
    "MammothJobFailedError",
    # Helpers
    "parse_path",
]
