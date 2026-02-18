"""
Connector and connection data models.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ConnectorInfo(BaseModel):
    """Information about a connector type."""

    model_config = ConfigDict(extra="allow")

    key: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    category: str | None = None


class ConnectionInfo(BaseModel):
    """Information about a specific connection."""

    model_config = ConfigDict(extra="allow")

    key: str | None = None
    connector_key: str | None = None
    name: str | None = None
    status: str | None = None
    config: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DsConfigInfo(BaseModel):
    """Information about a data source configuration."""

    model_config = ConfigDict(extra="allow")

    key: str | None = None
    connection_key: str | None = None
    name: str | None = None
    config: dict[str, Any] | None = None
    status: str | None = None
