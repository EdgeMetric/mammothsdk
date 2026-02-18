"""
Client Apps-related data models for the Mammoth Analytics SDK.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValueWrapper(BaseModel):
    """Wrapper for API values that come in {value: ...} format."""

    value: Any


class ClientAppSchema(BaseModel):
    """Schema for a client app object."""

    id: ValueWrapper | None = Field(None, description="Unique identifier for the client app")
    app_name: ValueWrapper | None = Field(None, description="Name of the client app")
    description: ValueWrapper | None = Field(None, description="Description of the client app")
    app_key: ValueWrapper | None = Field(None, description="Client key for API access")
    workspace_id: ValueWrapper | None = Field(None, description="Workspace ID")
    user_id: ValueWrapper | None = Field(None, description="User ID")
    project_id: ValueWrapper | None = Field(None, description="Project ID")
    last_usage: ValueWrapper | None = Field(
        None, description="Timestamp when the app was last used"
    )


class ClientAppsListResponse(BaseModel):
    """Schema for client apps API response."""

    result: list[ClientAppSchema] = Field(..., description="List of client app objects")


class ClientAppCreate(BaseModel):
    """Schema for creating a new client app."""

    app_name: str = Field(..., min_length=1, description="Name for the client app")
    description: str | None = Field(None, description="Optional description for the app")


class ClientAppPostResponse(BaseModel):
    """Schema for client app creation response."""

    client_app: ClientAppSchema = Field(..., description="Created client app details")
    message: str | None = Field(None, description="Success message")


class PatchOperation(BaseModel):
    """Schema for a single patch operation."""

    op: str = Field(..., description="Operation type (replace, add, remove)")
    path: str = Field(..., description="JSON path to the field")
    value: str | None = Field(None, description="New value for the field")


class PatchRequest(BaseModel):
    """Schema for patch request containing multiple operations."""

    patch: list[PatchOperation] = Field(..., description="List of patch operations")
