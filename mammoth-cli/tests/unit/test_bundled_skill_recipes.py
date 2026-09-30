from pathlib import Path

ROOT = (
    Path(__file__).parents[2]
    / "mammoth_cli"
    / "bundled_skill"
    / "mammoth-cli"
    / "references"
    / "recipes"
)


def test_recipe_index_and_required_topics_exist() -> None:
    index = (ROOT / "index.md").read_text(encoding="utf-8")
    for name in ("auth-scope", "resources", "transforms", "exports", "dashboards", "cleanup"):
        assert f"{name}.md" in index
        assert (ROOT / f"{name}.md").exists()


def test_recipes_are_discovery_led_and_machine_output_safe() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in ROOT.glob("*.md"))
    assert "schema get" in text
    # Piped output is JSON without flags; recipes must not re-teach the flags.
    assert "--output json --no-input" not in text
    assert "task_spec" not in text or "schema" in text
    assert "api_secret" not in text
    assert "standard JSON envelope" in text
    assert "structured error" in text


def test_dashboards_recipe_names_the_real_view_binding_field() -> None:
    """Truth-probe finding: a live `dashboard get` response has no
    `data.dataview_id` key -- the view binding is exposed as `data.sources`
    (a list of view ids). Following the old recipe verbatim gets an agent
    `None` back and could wrongly conclude no view is bound.
    """
    text = (ROOT / "dashboards.md").read_text(encoding="utf-8")
    assert "`data.sources`" in text
    assert "data.dataview_id" not in text


def test_dashboards_recipe_routes_per_dimension_asks_to_a_filter_control() -> None:
    text = (ROOT / "dashboards.md").read_text(encoding="utf-8")
    assert "dashboard filter add DASHBOARD_ID --input" in text
    assert "Do not build a copy of the board for each value" in text


def test_dashboards_recipe_hides_built_in_tiles_through_canvas_save() -> None:
    text = (ROOT / "dashboards.md").read_text(encoding="utf-8")
    assert "pages[0].hidden" in text and '"summary"' in text
    assert "dashboard canvas save DASHBOARD_ID" in text
    assert "only when asked to" not in text
