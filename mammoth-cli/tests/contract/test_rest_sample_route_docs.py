"""The REST import docs name the sample route that works.

Changelog analytics build, 2026-10-15: `recipes/rest-api-import.md` said
`connector connection query` "runs the same sample read-only" for a REST
source, and `dataset.create`'s restrictions offered it as an alternative. The
command runs one read-only SQL SELECT and refuses anything else before a
request is sent (`commands/connector.py` `_require_read_only_sql`), so an agent
that followed the recipe failed on its first try. The route that works is
`connector ds-config create ... {"data_sample": true}`.
"""

from pathlib import Path

import pytest

from mammoth_cli.commands.connector import _require_read_only_sql

_ROOT = Path(__file__).resolve().parents[2]
_RECIPES = _ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli" / "references" / "recipes"
_RECIPE = _RECIPES / "rest-api-import.md"
_DATASET = _ROOT / "spec" / "manifests" / "commands" / "dataset.yaml"
_REST_QUERY = '{"endpoint_path": "/posts", "data_root_path": "$", "max_pages": 1}'


def test_connection_query_refuses_a_rest_config() -> None:
    """The premise: if this ever accepts a REST config, the docs can say so again."""
    with pytest.raises(Exception):
        _require_read_only_sql(_REST_QUERY)


def test_the_rest_recipe_does_not_send_a_rest_sample_to_connection_query() -> None:
    step = _RECIPE.read_text(encoding="utf-8").split("## 2.", 1)[1].split("## 3.", 1)[0]
    assert "runs the same sample" not in step
    assert "ds-config create" in step and '"data_sample": true' in step


def test_dataset_create_does_not_offer_connection_query_for_rest() -> None:
    text = _DATASET.read_text(encoding="utf-8")
    rest = text.split("To import from a REST API", 1)[1].split("The recipe is", 1)[0]
    assert "or connector connection query" not in rest
