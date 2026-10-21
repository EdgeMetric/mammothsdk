"""Shared base class for SDK Pydantic models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MammothModel(BaseModel):
    """Base for all SDK models.

    ``defer_build`` postpones building each model's validator and serializer until first use,
    which keeps ``import mammoth`` fast. Subclass ``model_config`` is merged with this one.
    """

    model_config = ConfigDict(defer_build=True)
