"""
Folder-related data models for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FolderSchema(BaseModel):
    """Schema for a folder object."""

    id: int | None = Field(None, description="Unique identifier for the folder")
    name: str | None = Field(None, description="Name of the folder")
    status: str | None = Field(None, description="Current status of the folder")
    created_at: datetime | None = Field(None, description="Timestamp when the folder was created")
    updated_at: datetime | None = Field(
        None, description="Timestamp when the folder was last updated"
    )
    resource_id: str | int | None = Field(None, description="Resource ID of the folder")
    created_by: str | None = Field(None, description="User who created the folder")
    parent_id: int | None = Field(None, description="Parent folder ID")
    resource_path: str | None = Field(None, description="Resource path of the folder")


class FoldersList(BaseModel):
    """Schema for a list of folders with pagination."""

    folders: list[FolderSchema] = Field(..., description="List of folder objects")
    total: int = Field(..., description="Total number of folders")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class CreateFolder(BaseModel):
    """Schema for creating a new folder."""

    name: str = Field(..., min_length=1, description="Name for the new folder")
    parent_resource_id: str | None = Field(None, description="Parent folder resource ID")


class FolderDetails(BaseModel):
    """Schema for folder creation response."""

    folder: FolderSchema = Field(..., description="Created folder details")


class BulkFolderPatchRequest(BaseModel):
    """Schema for bulk folder operations (moving resources)."""

    source_folder_resource_id: str | None = Field(None, description="Source folder resource ID")
    target_folder_resource_id: str | None = Field(None, description="Target folder resource ID")
    resource_ids: list[str] = Field(..., description="List of resource IDs to move")
    operation: str = Field(..., description="Operation type (e.g., 'move')")
