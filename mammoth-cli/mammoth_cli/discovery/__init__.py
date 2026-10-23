"""Data files for command discovery: goal recipes, known limitations, next commands."""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any


@cache
def load_recipes() -> tuple[dict[str, Any], ...]:
    """The goal recipes shipped in the package.

    Returns:
        Every recipe in ``recipes.json``, in file order.
    """
    text = resources.files(__name__).joinpath("recipes.json").read_text("utf-8")
    return tuple(json.loads(text)["recipes"])
