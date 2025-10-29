"""
Client Apps-related data models for the Mammoth Analytics SDK.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ValueWrapper(BaseModel):
    """Wrapper for API values that come in {value: ...} format."""
    value: Any


class ClientAppSchema(BaseModel):
    """Schema for a client app object."""
    
    id: Optional[ValueWrapper] = Field(None, description="Unique identifier for the client app")
    app_name: Optional[ValueWrapper] = Field(None, description="Name of the client app")
    description: Optional[ValueWrapper] = Field(None, description="Description of the client app")
    app_key: Optional[ValueWrapper] = Field(None, description="Client key for API access")
    workspace_id: Optional[ValueWrapper] = Field(None, description="Workspace ID")
    user_id: Optional[ValueWrapper] = Field(None, description="User ID")
    project_id: Optional[ValueWrapper] = Field(None, description="Project ID")
    last_usage: Optional[ValueWrapper] = Field(None, description="Timestamp when the app was last used")


class ClientAppsListResponse(BaseModel):
    """Schema for client apps API response."""
    
    result: List[ClientAppSchema] = Field(..., description="List of client app objects")


class ClientAppCreate(BaseModel):
    """Schema for creating a new client app."""
    
    app_name: str = Field(..., min_length=1, description="Name for the client app")
    description: Optional[str] = Field(None, description="Optional description for the app")


class ClientAppPostResponse(BaseModel):
    """Schema for client app creation response."""
    
    client_app: ClientAppSchema = Field(..., description="Created client app details")
    message: Optional[str] = Field(None, description="Success message")


class PatchOperation(BaseModel):
    """Schema for a single patch operation."""
    
    op: str = Field(..., description="Operation type (replace, add, remove)")
    path: str = Field(..., description="JSON path to the field")
    value: Optional[str] = Field(None, description="New value for the field")


class PatchRequest(BaseModel):
    """Schema for patch request containing multiple operations."""
    
    patch: List[PatchOperation] = Field(..., description="List of patch operations")