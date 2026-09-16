from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel341_schema_preserves_release_overlay():
    s = get_schema("dashboard.assess-pbix")
    r = command_by_id("dashboard.assess-pbix")
    assert s and r and r["operation_ids"] == ["AssessPbix"]
    assert s["positionals"][0]["name"] == "file"
