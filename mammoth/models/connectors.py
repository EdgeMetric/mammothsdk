"""Connector and connection data models for the Mammoth Analytics SDK."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

# ── Read/response models (existing, kept as-is) ──────────────────────────────


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


# ── Connector create/update parameter models ──────────────────────────────────


class DsConfigPatchPath(str, Enum):
    """Allowed JSON-patch path values for ds_config update.

    Note: only ``query`` is fully implemented on the backend; the other paths
    are accepted in the enum for forward-compatibility but the server currently
    returns ``not_implemented_error`` for them.
    """

    QUERY = "query"
    PROFILE = "profile"
    ON_REFRESH_ACTION = "on_refresh_action"
    UNIQUE_SEQUENCE_COLUMN = "unique_sequence_column"


class DsConfigPatchOp(BaseModel):
    """A single JSON-patch operation for ds_config update.

    Attributes:
        op: Must be ``"replace"`` — the only supported operation.
        path: One of the :class:`DsConfigPatchPath` values.
        value: The replacement value; shape depends on ``path`` (e.g. for
            ``path='query'`` it is a dict containing at minimum ``query``,
            ``ds_id``, and ``validate``).
    """

    op: str
    path: DsConfigPatchPath
    value: Any
