"""
Folder-related data models for the Mammoth Analytics SDK.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FolderSchema(BaseModel):
    """Schema for a folder object."""
    
    id: Optional[int] = Field(None, description="Unique identifier for the folder")
    name: Optional[str] = Field(None, description="Name of the folder")
    status: Optional[str] = Field(None, description="Current status of the folder")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the folder was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the folder was last updated")
    resource_id: Optional[str] = Field(None, description="Resource ID of the folder")
    created_by: Optional[str] = Field(None, description="User who created the folder")
    parent_id: Optional[int] = Field(None, description="Parent folder ID")
    resource_path: Optional[str] = Field(None, description="Resource path of the folder")


class FoldersList(BaseModel):
    """Schema for a list of folders with pagination."""
    
    folders: List[FolderSchema] = Field(..., description="List of folder objects")
    total: int = Field(..., description="Total number of folders")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class CreateFolder(BaseModel):
    """Schema for creating a new folder."""
    
    name: str = Field(..., min_length=1, description="Name for the new folder")
    parent_resource_id: Optional[str] = Field(None, description="Parent folder resource ID")


class FolderDetails(BaseModel):
    """Schema for folder creation response."""
    
    folder: FolderSchema = Field(..., description="Created folder details")


class BulkFolderPatchRequest(BaseModel):
    """Schema for bulk folder operations (moving resources)."""
    
    source_folder_resource_id: Optional[str] = Field(None, description="Source folder resource ID")
    target_folder_resource_id: Optional[str] = Field(None, description="Target folder resource ID")
    resource_ids: List[str] = Field(..., description="List of resource IDs to move")
    operation: str = Field(..., description="Operation type (e.g., 'move')")