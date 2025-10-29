"""
Pydantic models for Dataviews API responses.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DataviewColumn(BaseModel):
    """Dataview column information."""
    model_config = ConfigDict(extra="allow")
    
    name: str
    type: Optional[str] = None
    nullable: Optional[bool] = None
    default_value: Optional[Any] = None


class DataviewProperties(BaseModel):
    """Dataview properties configuration."""
    model_config = ConfigDict(extra="allow")
    
    columns: Optional[List[DataviewColumn]] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    has_filters: Optional[bool] = None
    has_transforms: Optional[bool] = None


class DataviewSchema(BaseModel):
    """Dataview schema model."""
    model_config = ConfigDict(extra="allow")
    
    id: int
    name: str
    status: Optional[str] = None
    description: Optional[str] = None
    dataset_id: int
    properties: Optional[DataviewProperties] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None


class DataviewsList(BaseModel):
    """List of dataviews response."""
    model_config = ConfigDict(extra="allow")
    
    dataviews: List[DataviewSchema]
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class DataviewCreateRequest(BaseModel):
    """Dataview creation request."""
    model_config = ConfigDict(extra="allow")
    
    name: str
    description: Optional[str] = None
    clone_config_from: Optional[int] = None


class DataviewPatchData(BaseModel):
    """Dataview patch operation data."""
    model_config = ConfigDict(extra="allow")
    
    op: str  # "replace", "add", "remove"
    path: str
    value: Optional[Any] = None


class DataviewPatchRequest(BaseModel):
    """Dataview patch request."""
    model_config = ConfigDict(extra="allow")
    
    patch: List[DataviewPatchData]


class DataviewDataRequest(BaseModel):
    """Dataview data request (POST method)."""
    model_config = ConfigDict(extra="allow")
    
    sequence: Optional[int] = 0
    offset: Optional[int] = 1
    limit: Optional[int] = 400
    columns: Optional[List[str]] = None
    condition: Optional[Dict[str, Any]] = None
    sort: Optional[str] = None


class DataviewDataResponse(BaseModel):
    """Dataview data response."""
    model_config = ConfigDict(extra="allow")
    
    data: List[Dict[str, Any]]
    columns: Optional[List[str]] = None
    total_rows: Optional[int] = None
    offset: Optional[int] = None
    limit: Optional[int] = None
    sequence: Optional[int] = None


class ActiveUser(BaseModel):
    """Active user on dataview."""
    model_config = ConfigDict(extra="allow")
    
    user_id: int
    username: Optional[str] = None
    email: Optional[str] = None
    last_active: Optional[datetime] = None


class ActiveUsersList(BaseModel):
    """List of active users on dataview."""
    model_config = ConfigDict(extra="allow")
    
    users: List[ActiveUser]
    count: Optional[int] = None