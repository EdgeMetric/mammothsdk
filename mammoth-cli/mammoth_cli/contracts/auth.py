"""Strict request contract for `auth login`'s document input mode."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    """The strict `auth login --input` request document.

    Attributes:
        api_token: The ``mm_...`` API token (Bearer). Preferred.
        api_key: The deprecated Mammoth API key (with ``api_secret``).
        api_secret: The deprecated Mammoth API secret (with ``api_key``).
        workspace_id: A positive workspace id.
        server_prefix: An optional one-label server prefix; defaults to
            ``"app"`` when omitted.
    """

    model_config = ConfigDict(extra="forbid")

    api_token: str | None = Field(default=None, min_length=1)
    api_key: str | None = Field(default=None, min_length=1)
    api_secret: str | None = Field(default=None, min_length=1)
    workspace_id: int
    server_prefix: str | None = None

    @field_validator("workspace_id")
    @classmethod
    def _workspace_id_positive(cls, value: int) -> int:
        """Reject a nonpositive workspace id."""
        if value <= 0:
            raise ValueError("workspace_id must be a positive integer")
        return value

    @model_validator(mode="after")
    def _one_credential(self) -> LoginRequest:
        """Exactly one credential: an api_token, or an api_key + api_secret pair."""
        has_pair = self.api_key is not None or self.api_secret is not None
        if self.api_token is not None and has_pair:
            raise ValueError("give api_token, or api_key + api_secret, not both")
        if self.api_token is None and (self.api_key is None or self.api_secret is None):
            raise ValueError("api_token is required (or the deprecated api_key + api_secret)")
        return self
