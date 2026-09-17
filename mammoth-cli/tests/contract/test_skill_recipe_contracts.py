"""Keep packaged skill recipes tied to the published command manifest."""
from __future__ import annotations

import re
from pathlib import Path

from mammoth_cli.commands.capability import find_capabilities
from mammoth_cli.commands.schema import find_schemas
from mammoth_cli.manifest.loader import load_commands

ROOT = Path(__file__).parents[2]
SKILL_REFERENCES = ROOT / "mammoth_cli" / "bundled_skill" / "mammoth-cli" / "references"
RECIPES = SKILL_REFERENCES / "recipes"
SCHEMA_IDS = {str(record["command_id"]) for record in load_commands()}
FORBIDDEN_GUESSES = {
    "view.transform.deduplicate",
    "view.transform.type",
    "view.blend.create",
}


def test_recipe_schema_references_exist_in_published_manifest() -> None:
    for path in SKILL_REFERENCES.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for command_id in re.findall(r"mammoth schema get ([a-z0-9.-]+)", text):
            assert command_id in SCHEMA_IDS, (
                f"{path.name} references unavailable schema {command_id}"
            )


def test_skill_discovery_queries_have_published_matches() -> None:
    """Every literal discovery example in packaged references must work.

    Discovery is an AND-term search, so checking only recipes leaves router
    and operations examples able to dead-end a cold agent.
    """
    for path in SKILL_REFERENCES.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for query in re.findall(r'mammoth schema find "([^"]+)"', text):
            assert find_schemas(query)["matches"], (
                f"{path.name} discovery query has no match: {query!r}"
            )
        for query in re.findall(r'mammoth capability find "([^"]+)"', text):
            assert find_capabilities(query)["matches"], (
                f"{path.name} capability query has no match: {query!r}"
            )


def test_recipes_do_not_present_known_guessed_transform_aliases_as_routes() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in RECIPES.glob("*.md"))
    for command_id in FORBIDDEN_GUESSES:
        assert command_id not in text
