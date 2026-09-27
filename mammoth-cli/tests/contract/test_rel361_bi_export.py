"""Independent contract check for the release-only Power BI/Tableau file export binding."""

from mammoth_cli.commands.schema import get_schema
from mammoth_cli.manifest.loader import command_by_id


def test_rel361_schema_preserves_release_overlay() -> None:
    schema = get_schema("dashboard.bi-export")
    assert schema is not None
    record = command_by_id("dashboard.bi-export")
    assert record is not None
    assert record["operation_ids"] == ["PowerbiExport", "TableauExport"]
    assert record["sdk_symbol"] == "mammoth.api.dashboards.DashboardsAPI.export_powerbi"
    assert schema["positionals"][0]["name"] == "dashboard_id"
    field_names = {field["name"] for field in schema["accepted_fields"]}
    assert field_names == {"target", "output_path"}
    target_field = next(f for f in schema["accepted_fields"] if f["name"] == "target")
    assert target_field["required"] is True
    assert target_field["schema"]["enum"] == ["powerbi", "tableau"]
    output_path_field = next(f for f in schema["accepted_fields"] if f["name"] == "output_path")
    assert output_path_field["required"] is False
