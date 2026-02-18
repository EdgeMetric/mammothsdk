"""
Connector and connection data models.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ConnectorInfo(BaseModel):
    """Information about a connector type."""
    key: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None

    class Config:
        extra = "allow"


class ConnectionInfo(BaseModel):
    """Information about a specific connection."""
    key: Optional[str] = None
    connector_key: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        extra = "allow"


class DsConfigInfo(BaseModel):
    """Information about a data source configuration."""
    key: Optional[str] = None
    connection_key: Optional[str] = None
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

    class Config:
        extra = "allow"
