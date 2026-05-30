"""External-key data models for the Mammoth Analytics SDK."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ExternalKeyType(str, Enum):
    """LLM provider an external key authenticates against."""

    OPEN_AI = "open_ai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROK = "grok"


class ModelConfigSpec(BaseModel):
    """Optional per-key model configuration overrides.

    Only the fields you set are sent; unset fields fall back to the provider's
    defaults server-side.

    Attributes:
        thinking_budget: Token budget for extended thinking (>= -1; -1 = auto).
        thinking_level: Named thinking level (provider-specific).
        reasoning_effort: Named reasoning-effort level (provider-specific).
        web_search: Enable provider web search.
        cached_input: Enable input caching.
        batch_api: Route requests through the provider's batch API.
    """

    # The SDK never collides with Pydantic's own ``model_`` namespace here, but
    # silence the protected-namespace check since several fields are model-tuning.
    model_config = ConfigDict(protected_namespaces=())

    thinking_budget: int | None = Field(default=None, ge=-1)
    thinking_level: str | None = None
    reasoning_effort: str | None = None
    web_search: bool | None = None
    cached_input: bool | None = None
    batch_api: bool | None = None
