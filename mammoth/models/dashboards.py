"""
Dashboard data models.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class DashboardInfo(BaseModel):
    """Information about a dashboard."""
    id: Optional[int] = None
    name: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None

    class Config:
        extra = "allow"


class DashboardSource(BaseModel):
    """Dashboard data source information."""
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None

    class Config:
        extra = "allow"


class DashboardAnalytics(BaseModel):
    """Dashboard analytics information."""
    views: Optional[int] = None
    unique_users: Optional[int] = None
    last_viewed: Optional[str] = None

    class Config:
        extra = "allow"
