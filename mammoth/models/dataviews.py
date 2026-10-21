"""
Pydantic models for Dataviews API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict

from ._base import MammothModel


class DataviewColumn(MammothModel):
    """Dataview column information."""

    model_config = ConfigDict(extra="allow")

    name: str
    type: str | None = None
    nullable: bool | None = None
    default_value: Any | None = None


class DataviewProperties(MammothModel):
    """Dataview properties configuration."""

    model_config = ConfigDict(extra="allow")

    columns: list[DataviewColumn] | None = None
    row_count: int | None = None
    column_count: int | None = None
    has_filters: bool | None = None
    has_transforms: bool | None = None


class DataviewSchema(MammothModel):
    """Dataview schema model."""

    model_config = ConfigDict(extra="allow")

    id: int
    name: str
    status: str | None = None
    description: str | None = None
    dataset_id: int
    properties: DataviewProperties | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: int | None = None
    workspace_id: int | None = None
    project_id: int | None = None


class DataviewsList(MammothModel):
    """List of dataviews response."""

    model_config = ConfigDict(extra="allow")

    dataviews: list[DataviewSchema]
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class DataviewCreateRequest(MammothModel):
    """Dataview creation request."""

    model_config = ConfigDict(extra="allow")

    name: str
    description: str | None = None
    clone_config_from: int | None = None


class DataviewPatchData(MammothModel):
    """Dataview patch operation data."""

    model_config = ConfigDict(extra="allow")

    op: str  # "replace", "add", "remove"
    path: str
    value: Any | None = None


class DataviewPatchRequest(MammothModel):
    """Dataview patch request."""

    model_config = ConfigDict(extra="allow")

    patch: list[DataviewPatchData]


class DataviewDataRequest(MammothModel):
    """Dataview data request (POST method)."""

    model_config = ConfigDict(extra="allow")

    sequence: int | None = 0
    offset: int | None = 1
    limit: int | None = 400
    columns: list[str] | None = None
    condition: dict[str, Any] | None = None
    sort: str | None = None


class DataviewDataResponse(MammothModel):
    """Dataview data response."""

    model_config = ConfigDict(extra="allow")

    data: list[dict[str, Any]]
    columns: list[str] | None = None
    total_rows: int | None = None
    offset: int | None = None
    limit: int | None = None
    sequence: int | None = None


class ActiveUser(MammothModel):
    """Active user on dataview."""

    model_config = ConfigDict(extra="allow")

    user_id: int
    username: str | None = None
    email: str | None = None
    last_active: datetime | None = None


class ActiveUsersList(MammothModel):
    """List of active users on dataview."""

    model_config = ConfigDict(extra="allow")

    users: list[ActiveUser]
    count: int | None = None
