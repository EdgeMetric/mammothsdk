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


ProjectRole = Literal["project_admin", "project_analyst"]


class ProjectPatchOp(MammothModel):
    """One ``ProjectPatch`` operation; ``value`` is the new name or a properties object."""

    op: str = Field(..., min_length=1, max_length=50, description="Operation, e.g. replace")
    path: Literal["name", "properties", "agent_memory"] = Field(..., description="Field to change")
    value: str | dict[str, Any] = Field(..., description="New name, or project properties")


class ProjectPatch(MammothModel):
    """Schema for project patch operations."""

    patches: list[ProjectPatchOp] = Field(..., description="List of patch operations")


class AddUserSpec(MammothModel):
    """One user to add to a project, with their project role."""

    user_id: int = Field(..., gt=0, description="User id")
    role: ProjectRole = Field("project_analyst", description="Project role")


class AddUsersToProject(MammothModel):
    """Schema for adding users to a project."""

    users: list[AddUserSpec] = Field(..., description="Users to add, each with a project role")


class ProjectUserPatchOp(MammothModel):
    """The one ``ProjectUserPatch`` operation: replace the user's project role."""

    op: Literal["replace"] = "replace"
    path: Literal["permissions"] = "permissions"
    value: ProjectRole = Field(..., description="New project role")


class ProjectUserPatch(MammothModel):
    """Schema for updating user role in a project."""

    patch: list[ProjectUserPatchOp] = Field(..., description="Role change operations")


class UserRolesPatch(MammothModel):
    """A user and the project role to give them."""

    user_id: int | None = None
    role: ProjectRole | None = None


class InviteRolesPatch(MammothModel):
    """A pending invite and the project role to give it."""

    invite_id: int | None = None
    role: ProjectRole = "project_analyst"


class UsersToProjectsPatch(MammothModel):
    """The users and invites one ``ProjectsPatch`` operation applies to one project."""

    project_id: int | None = None
    user_ids: list[int] | None = None
    invite_ids: list[int] | None = None
    user_roles: list[UserRolesPatch] | None = None
    invite_roles: list[InviteRolesPatch] | None = None


class ProjectsPatchOp(MammothModel):
    """One ``ProjectsPatch`` operation: add, remove or replace roles across projects."""

    op: Literal["replace", "add", "remove"]
    path: Literal["role"] = "role"
    value: list[UsersToProjectsPatch]


class ProjectsPatch(MammothModel):
    """Schema for bulk project role changes."""

    patches: list[ProjectsPatchOp] = Field(..., description="Role operations across projects")


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
