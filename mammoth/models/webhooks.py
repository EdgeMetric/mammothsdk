"""
Webhook data models.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class WebhookInfo(BaseModel):
    """Information about a webhook."""
    id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    status: Optional[str] = None
    secret: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        extra = "allow"


class WebhookCreate(BaseModel):
    """Specification for creating a webhook."""
    name: str
    url: str
    events: List[str] = []
    secret: Optional[str] = None
