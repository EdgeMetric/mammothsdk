from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel356_schema_preserves_release_overlay() -> None:
    schema = get_schema("dashboard.templates.use")
    record = command_by_id("dashboard.templates.use")
    assert schema is not None and record is not None
    assert record["operation_ids"] == ["UseTemplate"]
    assert schema["request_model"] == "UseTemplateSpec"
    assert schema["result_model"] == "ObjectJobSchema | JobResponse"
    assert any(field["name"] == "body" for field in schema["accepted_fields"])
