from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel353_schema_preserves_release_overlay() -> None:
    schema = get_schema("dashboard.templates.pending")
    record = command_by_id("dashboard.templates.pending")
    assert schema is not None and record is not None
    assert record["operation_ids"] == ["DashboardV3TakePendingTemplate"]
    assert schema["request_model"] == "DashboardTemplatePendingRequest"
    assert schema["result_model"] == "PendingTemplateResponse"
