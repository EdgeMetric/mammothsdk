from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel340_schema_preserves_release_overlay():
    schema = get_schema("dashboard.import-workbook")
    record = command_by_id("dashboard.import-workbook")
    assert schema and record and record["operation_ids"] == ["ImportWorkbookDataset"]
    assert schema["positionals"][0]["name"] == "file"
    assert schema["agent_example"] == (
        "mammoth dashboard import-workbook sample.twbx --project 456 " "--yes --confirm 456"
    )
