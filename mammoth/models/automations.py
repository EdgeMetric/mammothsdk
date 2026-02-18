"""
Automation and schedule data models.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class AutomationInfo(BaseModel):
    """Information about an automation."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    status: str | None = None
    config: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ScheduleInfo(BaseModel):
    """Information about a schedule."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    name: str | None = None
    cron: str | None = None
    status: str | None = None
    next_run: str | None = None
    last_run: str | None = None
    config: dict[str, Any] | None = None
