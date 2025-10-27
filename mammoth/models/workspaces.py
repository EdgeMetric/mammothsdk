"""
Workspace-related data models for the Mammoth Analytics SDK.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WorkspaceSchema(BaseModel):
    """Schema for a workspace object."""
    
    id: Optional[int] = Field(None, description="Unique identifier for the workspace")
    name: Optional[str] = Field(None, description="Name of the workspace")
    status: Optional[str] = Field(None, description="Current status of the workspace")
    url: Optional[str] = Field(None, description="URL of the workspace")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the workspace was last updated")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the workspace was created")
    last_accessed: Optional[datetime] = Field(None, description="Timestamp when the workspace was last accessed")
    path: Optional[str] = Field(None, description="Path of the workspace")
    acc_image: Optional[str] = Field(None, description="Account image")
    date_format: Optional[str] = Field(None, description="Date format setting")
    total_users: Optional[int] = Field(None, description="Total number of users in the workspace")


class WorkspacesSchema(BaseModel):
    """Schema for a list of workspaces with pagination."""
    
    workspaces: List[WorkspaceSchema] = Field(..., description="List of workspace objects")
    total: int = Field(..., description="Total number of workspaces")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")