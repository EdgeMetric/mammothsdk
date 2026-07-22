"""Versioned success envelope for machine output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mammoth_cli import SCHEMA_VERSION

from .normalize import normalize


@dataclass
class Meta:
    command: str
    profile: str | None = None
    workspace_id: int | None = None
    project_id: int | None = None
    pagination: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "profile": self.profile,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "pagination": self.pagination,
        }


@dataclass
class Result:
    data: Any
    meta: Meta
    warnings: list[str] = field(default_factory=list)

    def to_envelope(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "data": normalize(self.data),
            "meta": self.meta.to_dict(),
        }
