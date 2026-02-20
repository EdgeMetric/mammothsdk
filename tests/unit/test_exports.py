"""Unit tests for ViewExport — verify handler_type and target_properties."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mammoth.view import View

# ── Fixtures ──────────────────────────────────────────────────

SAMPLE_VIEW_DATA = {
    "id": 1001,
    "name": "Export Test View",
    "properties": {
        "columns": [
            {"display_name": "col_a", "internal_name": "column_aaa", "type": "TEXT"},
        ],
    },
}


@pytest.fixture
def export_view(mock_client):
    """View with a mocked _create_export to capture export calls."""
    view = View(mock_client, SAMPLE_VIEW_DATA, 500)
    captured: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    def fake_create_export(handler_type, target_properties, **kwargs):
        captured.append((handler_type, target_properties, kwargs))
        return {"status": "created", "handler_type": handler_type}

    view.export._create_export = fake_create_export  # type: ignore[assignment]
    view.export._captured = captured  # type: ignore[attr-defined]
    return view


# ── Database exports ──────────────────────────────────────────


class TestToPostgres:
    def test_handler_type(self, export_view):
        export_view.export.to_postgres(
            host="db.example.com",
            port=5432,
            database="mydb",
            table="tbl",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "POSTGRES"
        assert target["host"] == "db.example.com"
        assert target["port"] == 5432
        assert target["database"] == "mydb"
        assert target["table"] == "tbl"
        assert target["username"] == "u"
        assert target["password"] == "p"


class TestToMysql:
    def test_handler_type(self, export_view):
        export_view.export.to_mysql(
            host="mysql.local",
            port=3306,
            database="mydb",
            table="tbl",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "MYSQL"
        assert target["host"] == "mysql.local"
        assert target["port"] == 3306


class TestToS3:
    def test_handler_and_defaults(self, export_view):
        export_view.export.to_s3()
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "S3"
        assert target["file_type"] == "csv"
        assert target["include_hidden"] is False
        assert target["is_format_set"] is True
        assert target["use_format"] is True
        # Auto-generated filename
        assert target["file"].startswith("view_1001_export_")

    def test_custom_filename(self, export_view):
        export_view.export.to_s3(file_name="data.csv", file_type="csv")
        _, target, _ = export_view.export._captured[-1]
        assert target["file"] == "data.csv"


class TestToFtp:
    def test_handler_type(self, export_view):
        export_view.export.to_ftp(
            host="ftp.example.com",
            path="/data/out.csv",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "FTP"
        assert target["port"] == 21
        assert target["path"] == "/data/out.csv"


class TestToSftp:
    def test_handler_type(self, export_view):
        export_view.export.to_sftp(
            host="sftp.example.com",
            path="/data/out.csv",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "SFTP"
        assert target["port"] == 22

    def test_custom_port(self, export_view):
        export_view.export.to_sftp(
            host="sftp.example.com",
            path="/data/out.csv",
            username="u",
            password="p",
            port=2222,
        )
        _, target, _ = export_view.export._captured[-1]
        assert target["port"] == 2222


class TestToEmail:
    def test_handler_type(self, export_view):
        export_view.export.to_email(recipients=["a@b.com", "c@d.com"])
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "EMAIL"
        assert target["recipients"] == ["a@b.com", "c@d.com"]


# ── Cloud / DB exports (kwargs-based) ────────────────────────


class TestToBigquery:
    def test_handler_type(self, export_view):
        export_view.export.to_bigquery(
            project_id="my-project",
            dataset="ds",
            table="tbl",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "BIGQUERY"
        assert target["project_id"] == "my-project"
        assert target["dataset"] == "ds"

    def test_control_keys_excluded_from_target(self, export_view):
        export_view.export.to_bigquery(
            project_id="proj",
            run_immediately=False,
            validate_only=True,
        )
        _, target, kwargs = export_view.export._captured[-1]
        assert "run_immediately" not in target
        assert "validate_only" not in target
        # But they're forwarded as kwargs
        assert kwargs["run_immediately"] is False
        assert kwargs["validate_only"] is True


class TestToRedshift:
    def test_handler_type(self, export_view):
        export_view.export.to_redshift(host="rs.aws.com", database="db", table="t")
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "REDSHIFT"
        assert target["host"] == "rs.aws.com"


class TestToElasticsearch:
    def test_handler_type(self, export_view):
        export_view.export.to_elasticsearch(host="es.local", index="idx")
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "ELASTICSEARCH"
        assert target["index"] == "idx"


class TestPublishToDb:
    def test_handler_type(self, export_view):
        export_view.export.publish_to_db(host="db.local", table="pub")
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "PUBLISHDB"
        assert target["table"] == "pub"


# ── Dataset export ────────────────────────────────────────────


class TestToDataset:
    def test_handler_type(self, export_view):
        export_view.export.to_dataset(dest_dataset_id=42)
        handler, target, _ = export_view.export._captured[-1]
        assert handler == "INTERNAL_DATASET"
        assert target["dataset_name"] == "42"

    def test_with_column_mapping(self, export_view):
        mapping = {"col_a": "mapped_col"}
        export_view.export.to_dataset(dest_dataset_id=42, column_mapping=mapping)
        _, target, _ = export_view.export._captured[-1]
        assert target["COLUMN_MAPPING"] == mapping


# ── CSV export ────────────────────────────────────────────────


class TestToCsv:
    def test_delegates_to_client(self, export_view):
        mock_path = Path("/tmp/test.csv")
        export_view._client.exports = MagicMock()
        export_view._client.exports.to_csv = MagicMock(return_value=mock_path)

        result = export_view.export.to_csv(output_path="/tmp/test.csv", timeout=120)

        export_view._client.exports.to_csv.assert_called_once_with(
            dataview_id=1001,
            output_path="/tmp/test.csv",
            timeout=120,
            dataset_id=500,
        )
        assert result == mock_path


# ── List and delete ───────────────────────────────────────────


class TestExportList:
    def test_list_from_dict(self, export_view):
        export_view._client.exports = MagicMock()
        export_view._client.exports.list = MagicMock(
            return_value={"exports": [{"id": 1}, {"id": 2}]}
        )
        result = export_view.export.list()
        assert len(result) == 2
        assert result[0]["id"] == 1

    def test_list_from_model(self, export_view):
        """Test when API returns a model with .exports attribute."""
        mock_resp = MagicMock()
        mock_resp.exports = [{"id": 10}]
        export_view._client.exports = MagicMock()
        export_view._client.exports.list = MagicMock(return_value=mock_resp)
        result = export_view.export.list()
        assert result == [{"id": 10}]


class TestExportDelete:
    def test_delete(self, export_view):
        export_view._client._request_json = MagicMock(return_value={"status": "deleted"})
        result = export_view.export.delete(export_id=99)
        assert result["status"] == "deleted"
        export_view._client._request_json.assert_called_once()
        call_args = export_view._client._request_json.call_args
        assert call_args[0][0] == "DELETE"
        assert "/exports/99" in call_args[0][1]

    def test_delete_requires_project_id(self, export_view):
        export_view._client.project_id = None
        with pytest.raises(ValueError, match="project_id"):
            export_view.export.delete(export_id=99)
