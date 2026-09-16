"""Typed release batch creation request models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ColumnNameMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination_c_name: str
    source_c_name: str
    expected_destination_c_type: Literal["TEXT", "NUMERIC", "DATE"]


class ColumnIdMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_c_id: str
    expected_destination_c_type: Literal["TEXT", "NUMERIC", "DATE"]
    destination_c_id: str | None = None
    action: Literal["add_column"] | None = None


class NewDsDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class ProjectedSourceColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    internal_name: str
    type: Literal["TEXT", "NUMERIC", "DATE"]


class BatchesPostRequest(BaseModel):
    """Release ``BatchesPostRequest`` with its source/file alternatives."""

    model_config = ConfigDict(extra="forbid")

    source_id: int | None = Field(None, description="Source dataset ID")
    mapping: list[ColumnNameMapping] | list[ColumnIdMapping] | None = None
    validate_only: bool = False
    delete_source_ds: bool = False
    new_ds_details: NewDsDetails | None = None
    file_id: int | None = None
    projected_source_schema: list[ProjectedSourceColumn] | None = None
