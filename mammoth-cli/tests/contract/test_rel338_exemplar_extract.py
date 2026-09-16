"""Independent contract check for the release-only exemplar extraction binding."""

from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel338_schema_preserves_release_overlay() -> None:
    schema = get_schema("dashboard.exemplar.extract")
    assert schema is not None
    record = command_by_id("dashboard.exemplar.extract")
    assert record is not None
    assert record["operation_ids"] == ["ExtractExemplar"]
    assert schema["request_model"] == "ExemplarExtractSpec"
    assert schema["result_model"] == "ExemplarExtractResponse"
    assert schema["accepted_fields"][0]["name"] == "body"
    assert schema["accepted_fields"][0]["required"] is True
