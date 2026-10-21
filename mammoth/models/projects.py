"""
Project-related data models for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field

from ._base import MammothModel


class ProjectProperties(MammothModel):
    """Schema for project properties."""

    # This can be extended based on actual project properties structure
    pass


class ProjectSchema(MammothModel):
    """Schema for a project object."""

    id: int | None = Field(None, description="Unique identifier for the project")
    name: str | None = Field(None, description="Name of the project")
    status: str | None = Field(None, description="Current status of the project")
    created_at: datetime | None = Field(None, description="Timestamp when the project was created")
    updated_at: datetime | None = Field(
        None, description="Timestamp when the project was last updated"
    )
    properties: ProjectProperties | None = Field(None, description="Project properties")
    owner_workspace_id: int | None = Field(
        None, description="ID of the workspace that owns this project"
    )


class ProjectList(MammothModel):
    """Schema for a list of projects with pagination."""

    projects: list[ProjectSchema] = Field(..., description="List of project objects")
    total: int = Field(..., description="Total number of projects")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class ProjectCreate(MammothModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, description="Name for the new project")
    description: str | None = Field(None, description="Optional description for the project")


class PatchOperation(MammothModel):
    """Schema for a single patch operation."""

    op: str = Field(..., description="Operation type (replace, add, remove)")
    path: str = Field(..., description="JSON path to the field")
    value: Any | None = Field(None, description="New value for the field")


class ProjectPatch(MammothModel):
    """Schema for project patch operations."""

    patch: list[PatchOperation] = Field(..., description="List of patch operations")


class AddUsersToProject(MammothModel):
    """Schema for adding users to a project."""

    user_emails: list[str] = Field(..., description="List of user email addresses to add")
    role: str | None = Field("editor", description="Role for the users (editor, admin)")


class ProjectUserPatch(MammothModel):
    """Schema for updating user role in a project."""

    role: str = Field(..., description="New role for the user (editor, admin)")


class ProjectsPatch(MammothModel):
    """Schema for bulk project operations."""

    project_ids: list[int] = Field(..., description="List of project IDs to update")
    operations: list[PatchOperation] = Field(..., description="Operations to perform on projects")


class DataSyncPatchValue(MammothModel):
    """Target and desired data-sync settings for one resource."""

    model_config = ConfigDict(extra="forbid")

    context_type: Literal["dataview", "task", "action"]
    context_id: int
    data_pass_through: bool | None = None
    run_pending_update: bool | None = None


class DataSyncPatchItem(MammothModel):
    """One release-defined data-sync JSON-PATCH operation."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["replace"]
    path: Literal["data_sync"]
    value: DataSyncPatchValue


class DataSyncPatchRequest(MammothModel):
    """Typed request for bulk resource data-sync updates."""

    model_config = ConfigDict(extra="forbid")

    patches: list[DataSyncPatchItem] = Field(min_length=1)
