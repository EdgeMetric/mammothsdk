"""
Pydantic models for Datasets API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DatasetProperties(BaseModel):
    """Dataset properties configuration."""

    model_config = ConfigDict(extra="allow")

    file_type: str | None = None
    encoding: str | None = None
    delimiter: str | None = None
    has_headers: bool | None = None
    row_count: int | None = None
    column_count: int | None = None
    file_size: int | None = None


class DatasetSchema(BaseModel):
    """Dataset schema model."""

    model_config = ConfigDict(extra="allow")

    id: int
    name: str
    status: str | None = None
    description: str | None = None
    properties: DatasetProperties | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: int | None = None
    workspace_id: int | None = None
    project_id: int | None = None
    folder_id: int | None = None


class DatasetsList(BaseModel):
    """List of datasets response."""

    model_config = ConfigDict(extra="allow")

    datasets: list[DatasetSchema]
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class DatasetCreateSpec(BaseModel):
    """Dataset creation specification."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    description: str | None = None
    source_type: str  # e.g., "file", "url", "database"
    source_config: dict[str, Any]
    properties: DatasetProperties | None = None


class DatasetPatchData(BaseModel):
    """Dataset patch operation data."""

    model_config = ConfigDict(extra="allow")

    op: str  # "replace", "add", "remove"
    path: str
    value: Any | None = None


class DatasetPatchRequest(BaseModel):
    """Dataset patch request."""

    model_config = ConfigDict(extra="allow")

    patch: list[DatasetPatchData]


class DatasetDataResponse(BaseModel):
    """Dataset data response."""

    model_config = ConfigDict(extra="allow")

    data: list[dict[str, Any]]
    columns: list[str] | None = None
    total_rows: int | None = None
    offset: int | None = None
    limit: int | None = None
