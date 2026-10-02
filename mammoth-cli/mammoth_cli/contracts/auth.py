"""Strict request contract for `auth login`'s document input mode."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """The strict `auth login --input` request document.

    Attributes:
        api_token: The ``mm_...`` API token (sent as ``Authorization: Bearer``).
        server_prefix: An optional one-label server prefix; defaults to
            ``"app"`` when omitted.
    """

    model_config = ConfigDict(extra="forbid")

    api_token: str = Field(min_length=1)
    server_prefix: str | None = None
