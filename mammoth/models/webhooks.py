"""
Webhook data models.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WebhookInfo(BaseModel):
    """Information about a webhook."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    url: str | None = None
    events: list[str] | None = None
    status: str | None = None
    secret: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class WebhookCreate(BaseModel):
    """Specification for creating a webhook."""

    name: str
    url: str
    events: list[str] = []
    secret: str | None = None
