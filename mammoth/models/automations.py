"""
Automation and schedule data models.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class AutomationInfo(BaseModel):
    """Information about an automation."""
    id: Optional[int] = None
    name: Optional[str] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        extra = "allow"


class ScheduleInfo(BaseModel):
    """Information about a schedule."""
    id: Optional[int] = None
    name: Optional[str] = None
    cron: Optional[str] = None
    status: Optional[str] = None
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"
