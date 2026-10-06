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
    """Schema for a client app object.

    Every field is optional because ``fields=`` narrows what the API returns.
    Values are plain, as apiv2 sends them (not ``{"value": ...}`` wrapped).
    """

    id: int | None = Field(None, description="Unique identifier for the client app")
    app_name: str | None = Field(None, description="Name of the client app")
    description: str | None = Field(None, description="Description of the client app")
    app_key: str | None = Field(None, description="Client key for API access")
    type: str | None = Field(None, description="Credential type (token or legacy)")
    workspace_id: int | None = Field(None, description="Workspace ID")
    user_id: int | None = Field(None, description="User ID")
    project_id: int | None = Field(None, description="Project ID")
    last_usage: str | None = Field(None, description="Timestamp when the app was last used")
    created_at: str | None = Field(None, description="Timestamp when the app was created")


class ClientAppsListResponse(BaseModel):
    """Schema for client apps API response."""

    result: list[ClientAppSchema] = Field(..., description="List of client app objects")


class ClientAppCreate(BaseModel):
    """Schema for creating a new client app."""

    app_name: str = Field(..., min_length=1, description="Name for the client app")
    description: str = Field("", description="Description for the app (the API requires the field)")


class ClientAppPostResponse(BaseModel):
    """Schema for client app creation response (flat; carries the one-time token)."""

    app_name: str = Field(..., description="Name of the client app")
    app_key: str = Field(..., description="Client key for API access")
    description: str = Field(..., description="Description of the client app")
    workspace_id: int = Field(..., description="Workspace ID")
    user_id: int = Field(..., description="User ID")
    token: str = Field(
        ..., description="Plaintext Bearer token, returned once and never recoverable"
    )


class PatchOperation(BaseModel):
    """Schema for a single patch operation."""

    op: str = Field(..., description="Operation type (replace, add, remove)")
    path: str = Field(..., description="JSON path to the field")
    value: str | None = Field(None, description="New value for the field")


class PatchRequest(BaseModel):
    """Schema for patch request containing multiple operations."""

    patch: list[PatchOperation] = Field(..., description="List of patch operations")
