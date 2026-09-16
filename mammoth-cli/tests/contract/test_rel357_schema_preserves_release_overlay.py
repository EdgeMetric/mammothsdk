from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel357_schema_preserves_release_overlay():
    s = get_schema("dashboard.assess-twb")
    r = command_by_id("dashboard.assess-twb")
    assert s and r and r["operation_ids"] == ["AssessTwb"]
    assert s["positionals"][0]["name"] == "file"
