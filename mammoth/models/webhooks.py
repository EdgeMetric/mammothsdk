"""
Webhook data models matching the backend WebhookStandardSchema / WebhookSpec.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class WebhookMode(str, Enum):
    """Webhook data ingestion mode."""

    REPLACE = "replace"
    COMBINE = "combine"


class WebhookInfo(BaseModel):
    """Information about a webhook dataset (matches WebhookStandardSchema)."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    mode: str | None = None
    uri: str | None = None
    ds_id: int | None = None
    origins: str | None = None
    secret: str | None = None


class WebhookCreate(BaseModel):
    """Specification for creating a webhook dataset (matches WebhookSpec)."""

    name: str = "Generic Webhook"
    mode: WebhookMode = WebhookMode.REPLACE
    folder_resource_id: str | None = None
    origins: str = "*"
    is_secure: bool = False
