"""Workspace-related data models for the Mammoth Analytics SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


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


# ── workspace.update patch models ─────────────────────────────────────────────


class BillingCycle(str, Enum):
    """Allowed values for the ``billing_cycle`` workspace patch path."""

    MONTHLY = "monthly"
    YEARLY = "yearly"
    ANNUAL = "annual"


class WorkspacePatchPath(str, Enum):
    """Allowed JSON-patch path values for workspace update."""

    NAME = "name"
    METADATA = "metadata"
    PLAN_ID = "plan_id"
    BILLING_CYCLE = "billing_cycle"


class WorkspacePatchOp(BaseModel):
    """A single JSON-patch operation for workspace update.

    Attributes:
        op: Must be ``"replace"`` — the only supported operation.
        path: One of the :class:`WorkspacePatchPath` values.
        value: Type depends on ``path``:

            - ``name``: ``str``, 1–50 characters.
            - ``metadata``: ``dict``.
            - ``plan_id``: ``int``.
            - ``billing_cycle``: :class:`BillingCycle` (``monthly``, ``yearly``,
              or ``annual``).
    """

    op: str
    path: WorkspacePatchPath
    value: Any

    @model_validator(mode="after")
    def _validate_value_type(self) -> WorkspacePatchOp:
        path = self.path
        v = self.value
        if path is WorkspacePatchPath.NAME:
            if not isinstance(v, str) or not (1 <= len(v) <= 50):
                raise ValueError("name value must be a string of 1–50 characters")
        elif path is WorkspacePatchPath.METADATA:
            if not isinstance(v, dict):
                raise ValueError("metadata value must be a dict")
        elif path is WorkspacePatchPath.PLAN_ID:
            if not isinstance(v, int):
                raise ValueError("plan_id value must be an int")
        elif path is WorkspacePatchPath.BILLING_CYCLE:
            allowed = {e.value for e in BillingCycle}
            if v not in allowed:
                raise ValueError(f"billing_cycle value must be one of {sorted(allowed)}, got {v!r}")
        return self


# ── workspace.update_user patch models ────────────────────────────────────────


class WorkspaceRoleType(str, Enum):
    """Allowed role values for workspace user patch operations."""

    WORKSPACE_MEMBER = "workspace_member"
    WORKSPACE_ADMIN = "workspace_admin"
    WORKSPACE_OWNER = "workspace_owner"
    WORKSPACE_GUEST = "workspace_guest"


class UserRolePatchOp(BaseModel):
    """A single JSON-patch operation for workspace user update.

    Attributes:
        op: Must be ``"replace"`` — the only supported operation.
        path: Must be ``"role"`` — the only patchable field for per-user PATCH.
        value: A :class:`WorkspaceRoleType` value.
    """

    op: str
    path: str
    value: WorkspaceRoleType

    @field_validator("path")
    @classmethod
    def _validate_path(cls, v: str) -> str:
        if v != "role":
            raise ValueError(f"path must be 'role', got {v!r}")
        return v
