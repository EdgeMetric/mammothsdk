"""Independent contract check for the release-only context extraction binding."""

from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel337_schema_preserves_release_overlay() -> None:
    schema = get_schema("dashboard.context.extract")
    assert schema is not None
    record = command_by_id("dashboard.context.extract")
    assert record is not None
    assert record["operation_ids"] == ["ExtractContext"]
    assert schema["request_model"] == "ContextExtractSpec"
    assert schema["result_model"] == "ContextExtractResponse"
    assert schema["accepted_fields"][0]["name"] == "body"
    assert schema["accepted_fields"][0]["required"] is True
