from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel359_schema_preserves_release_overlay() -> None:
    schema = get_schema("dashboard.swap-data")
    record = command_by_id("dashboard.swap-data")
    assert schema is not None and record is not None
    assert record["operation_ids"] == ["SwapDashboardData"]
    assert schema["request_model"] == "SwapDataSpec"
    assert schema["accepted_fields"][0]["name"] == "body"
