"""Strict request contract for `auth login`'s document input mode."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    """The strict `auth login --input` request document.

    Attributes:
        api_key: The Mammoth API key.
        api_secret: The Mammoth API secret.
        workspace_id: A positive workspace id.
        server_prefix: An optional one-label server prefix; defaults to
            ``"app"`` when omitted.
    """

    model_config = ConfigDict(extra="forbid")

    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)
    workspace_id: int
    server_prefix: str | None = None

    @field_validator("workspace_id")
    @classmethod
    def _workspace_id_positive(cls, value: int) -> int:
        """Reject a nonpositive workspace id."""
        if value <= 0:
            raise ValueError("workspace_id must be a positive integer")
        return value
