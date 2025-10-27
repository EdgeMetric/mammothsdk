"""
Pydantic models for Datasets API responses.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DatasetProperties(BaseModel):
    """Dataset properties configuration."""
    model_config = ConfigDict(extra="allow")
    
    file_type: Optional[str] = None
    encoding: Optional[str] = None
    delimiter: Optional[str] = None
    has_headers: Optional[bool] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    file_size: Optional[int] = None


class DatasetSchema(BaseModel):
    """Dataset schema model."""
    model_config = ConfigDict(extra="allow")
    
    id: int
    name: str
    status: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[DatasetProperties] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    folder_id: Optional[int] = None


class DatasetsList(BaseModel):
    """List of datasets response."""
    model_config = ConfigDict(extra="allow")
    
    datasets: List[DatasetSchema]
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class DatasetCreateSpec(BaseModel):
    """Dataset creation specification."""
    model_config = ConfigDict(extra="allow")
    
    name: Optional[str] = None
    description: Optional[str] = None
    source_type: str  # e.g., "file", "url", "database"
    source_config: Dict[str, Any]
    properties: Optional[DatasetProperties] = None


class DatasetPatchData(BaseModel):
    """Dataset patch operation data."""
    model_config = ConfigDict(extra="allow")
    
    op: str  # "replace", "add", "remove"
    path: str
    value: Optional[Any] = None


class DatasetPatchRequest(BaseModel):
    """Dataset patch request."""
    model_config = ConfigDict(extra="allow")
    
    patch: List[DatasetPatchData]


class DatasetDataResponse(BaseModel):
    """Dataset data response."""
    model_config = ConfigDict(extra="allow")
    
    data: List[Dict[str, Any]]
    columns: Optional[List[str]] = None
    total_rows: Optional[int] = None
    offset: Optional[int] = None
    limit: Optional[int] = None