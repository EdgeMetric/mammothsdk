"""
Workspace-related data models for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceSchema(BaseModel):
    """Schema for a workspace object."""

    id: int | None = Field(None, description="Unique identifier for the workspace")
    name: str | None = Field(None, description="Name of the workspace")
    status: str | None = Field(None, description="Current status of the workspace")
    url: str | None = Field(None, description="URL of the workspace")
    updated_at: datetime | None = Field(
        None, description="Timestamp when the workspace was last updated"
    )
    created_at: datetime | None = Field(
        None, description="Timestamp when the workspace was created"
    )
    last_accessed: datetime | None = Field(
        None, description="Timestamp when the workspace was last accessed"
    )
    path: str | None = Field(None, description="Path of the workspace")
    acc_image: str | None = Field(None, description="Account image")
    date_format: str | None = Field(None, description="Date format setting")
    total_users: int | None = Field(None, description="Total number of users in the workspace")


class WorkspacesSchema(BaseModel):
    """Schema for a list of workspaces with pagination."""

    workspaces: list[WorkspaceSchema] = Field(..., description="List of workspace objects")
    total: int = Field(..., description="Total number of workspaces")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")
