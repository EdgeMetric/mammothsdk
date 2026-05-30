"""Unit tests for ViewExport — verify handler_type and target_properties."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mammoth.condition import Condition
from mammoth.exceptions import MammothExportError, MammothValidationError
from mammoth.models.exports import (
    BigQueryExportType,
    ExportStatus,
    HandlerType,
    HttpMethod,
    OdbcType,
    RestAuthType,
)
from mammoth.models.pipeline import ExportFileType, Operator, SaveAsDatasetMode
from mammoth.view import (
    ERR_BIGQUERY_UPSERT_KEYS,
    ERR_EMAIL_NO_RECIPIENTS,
    ERR_REST_BATCH_SIZE,
    ERR_REST_TIMEOUT,
    ERR_SFTP_KEY_REQUIRED,
    View,
)

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
#
# Each test pins the EXACT handler_type enum and the COMPLETE
# target_properties dict (==, not subset). An equality check fails on a
# missing key, a renamed key, AND an unexpected extra key — which is the
# precise regression guard for the per-handler wire-key drift these methods
# had (ftp host->domain/path->directory+file, email recipients->emails,
# bigquery snake->camelCase, powerbi client_id->clientId).


class TestToPostgres:
    def test_emits_exact_target(self, export_view):
        export_view.export.to_postgres(
            host="db.example.com",
            port=5432,
            database="mydb",
            table="tbl",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.POSTGRES
        assert target == {
            "host": "db.example.com",
            "port": 5432,
            "database": "mydb",
            "table": "tbl",
            "username": "u",
            "password": "p",
        }

    def test_control_kwargs_not_leaked_into_target(self, export_view):
        # run_immediately / validate_only are export-control flags, not wire
        # properties: they must ride **kwargs to _create_export, never the
        # target_properties payload.
        export_view.export.to_postgres(
            host="h",
            port=5432,
            database="d",
            table="t",
            username="u",
            password="p",
            run_immediately=False,
            validate_only=True,
        )
        _, target, kwargs = export_view.export._captured[-1]
        assert "run_immediately" not in target
        assert "validate_only" not in target
        assert kwargs["run_immediately"] is False
        assert kwargs["validate_only"] is True


class TestToMysql:
    def test_emits_exact_target(self, export_view):
        export_view.export.to_mysql(
            host="mysql.local",
            port=3306,
            database="mydb",
            table="tbl",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.MYSQL
        assert target == {
            "host": "mysql.local",
            "port": 3306,
            "database": "mydb",
            "table": "tbl",
            "username": "u",
            "password": "p",
        }


class TestToMssql:
    def test_emits_exact_target(self, export_view):
        export_view.export.to_mssql(
            host="sql.local",
            port=1433,
            database="mydb",
            table="tbl",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.MSSQL
        assert target == {
            "host": "sql.local",
            "port": 1433,
            "database": "mydb",
            "table": "tbl",
            "username": "u",
            "password": "p",
        }


class TestToRedshift:
    def test_emits_exact_target(self, export_view):
        export_view.export.to_redshift(
            host="rs.aws.com",
            port=5439,
            database="db",
            table="t",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.REDSHIFT
        assert target == {
            "host": "rs.aws.com",
            "port": 5439,
            "database": "db",
            "table": "t",
            "username": "u",
            "password": "p",
        }


class TestToS3:
    def test_handler_and_defaults(self, export_view):
        export_view.export.to_s3()
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.S3
        assert target["file_type"] == "csv"
        assert target["include_hidden"] is False
        assert target["is_format_set"] is True
        assert target["use_format"] is True
        # Auto-generated filename embeds the dataview id and a timestamp.
        assert target["file"].startswith("view_1001_export_")
        # Exactly these keys — no stray control flags leaked in.
        assert set(target) == {
            "file",
            "file_type",
            "include_hidden",
            "is_format_set",
            "use_format",
        }

    def test_custom_filename(self, export_view):
        export_view.export.to_s3(file_name="data.csv", file_type=ExportFileType.CSV)
        _, target, _ = export_view.export._captured[-1]
        assert target["file"] == "data.csv"

    def test_json_file_type(self, export_view):
        export_view.export.to_s3(file_type=ExportFileType.JSON)
        _, target, _ = export_view.export._captured[-1]
        assert target["file_type"] == "json"

    def test_parquet_file_type(self, export_view):
        export_view.export.to_s3(file_type=ExportFileType.PARQUET)
        _, target, _ = export_view.export._captured[-1]
        assert target["file_type"] == "parquet"


class TestToFtp:
    def test_emits_domain_directory_file_not_host_path(self, export_view):
        # Regression guard: the old stub emitted host/path; the backend reads
        # domain/directory/file. Lock the exact key set + default port.
        export_view.export.to_ftp(
            domain="ftp.example.com",
            directory="/exports",
            file="sales.csv",
            username="u",
            password="p",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.FTP
        assert target == {
            "domain": "ftp.example.com",
            "port": 21,
            "directory": "/exports",
            "file": "sales.csv",
            "username": "u",
            "password": "p",
        }
        assert "host" not in target
        assert "path" not in target

    def test_custom_port(self, export_view):
        export_view.export.to_ftp(
            domain="ftp.example.com",
            directory="/exports",
            file="sales.csv",
            username="u",
            password="p",
            port=2121,
        )
        _, target, _ = export_view.export._captured[-1]
        assert target["port"] == 2121


class TestToSftp:
    def test_password_auth_emits_password_not_key_fields(self, export_view):
        export_view.export.to_sftp(
            host="sftp.example.com",
            username="u",
            password="p",
            directory="/out",
            file_name="data.csv",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.SFTP
        assert target == {
            "host": "sftp.example.com",
            "port": 22,
            "username": "u",
            "directory": "/out",
            "file_name": "data.csv",
            "randomize_file_name": False,
            "ssh_key_authentication": False,
            "password": "p",
        }
        # Key-auth fields must be absent in password mode.
        assert "private_key" not in target
        assert "passphrase" not in target

    def test_key_auth_emits_private_key_not_password(self, export_view):
        export_view.export.to_sftp(
            host="sftp.example.com",
            username="u",
            ssh_key_authentication=True,
            private_key="-----BEGIN KEY-----",
            passphrase="secret",
        )
        _, target, _ = export_view.export._captured[-1]
        assert target["ssh_key_authentication"] is True
        assert target["private_key"] == "-----BEGIN KEY-----"
        assert target["passphrase"] == "secret"
        # Password must NOT be emitted when authenticating with a key.
        assert "password" not in target

    def test_custom_port(self, export_view):
        export_view.export.to_sftp(
            host="sftp.example.com",
            username="u",
            password="p",
            port=2222,
        )
        _, target, _ = export_view.export._captured[-1]
        assert target["port"] == 2222

    def test_key_auth_without_private_key_rejected(self, export_view):
        with pytest.raises(MammothValidationError) as exc:
            export_view.export.to_sftp(
                host="sftp.example.com",
                username="u",
                ssh_key_authentication=True,
            )
        assert exc.value.message == ERR_SFTP_KEY_REQUIRED
        assert not export_view.export._captured


class TestToEmail:
    def test_emits_emails_not_recipients(self, export_view):
        # Regression guard: the old stub emitted "recipients"; the backend
        # reads "emails".
        export_view.export.to_email(emails=["a@b.com", "c@d.com"])
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.EMAIL
        assert target == {"emails": ["a@b.com", "c@d.com"]}
        assert "recipients" not in target

    def test_optional_fields_only_when_truthy(self, export_view):
        export_view.export.to_email(
            emails=["a@b.com"],
            subject="Q1 report",
            message="See attached",
            resource="Sales",
        )
        _, target, _ = export_view.export._captured[-1]
        assert target == {
            "emails": ["a@b.com"],
            "subject": "Q1 report",
            "message": "See attached",
            "resource": "Sales",
        }

    def test_empty_recipients_rejected(self, export_view):
        with pytest.raises(MammothValidationError) as exc:
            export_view.export.to_email(emails=[])
        assert exc.value.message == ERR_EMAIL_NO_RECIPIENTS
        assert not export_view.export._captured


class TestToBigquery:
    def test_emits_camelcase_export_type(self, export_view):
        # Regression guard: backend reads camelCase exportType; selection is
        # by profile/identity, not raw project_id/dataset.
        profile = {"name": "ds", "value": [["proj", "ds"]]}
        identity = {"identity_config": {}, "host": "sa@x.iam"}
        export_view.export.to_bigquery(
            selected_profile=profile,
            selected_identity=identity,
            table="tbl",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.BIGQUERY
        assert target == {
            "selected_profile": profile,
            "selected_identity": identity,
            "table": "tbl",
            "exportType": "REPLACE",
        }
        assert "exportType" in target
        assert "export_type" not in target

    def test_upsert_emits_upsert_keys(self, export_view):
        keys = [{"column": {"display_name": "id"}}]
        export_view.export.to_bigquery(
            selected_profile={},
            selected_identity={},
            table="t",
            export_type=BigQueryExportType.UPSERT,
            upsert_keys=keys,
        )
        _, target, _ = export_view.export._captured[-1]
        assert target["exportType"] == "UPSERT"
        assert target["upsertKeys"] == keys

    def test_no_optional_keys_when_omitted(self, export_view):
        export_view.export.to_bigquery(selected_profile={}, selected_identity={}, table="t")
        _, target, _ = export_view.export._captured[-1]
        assert "upsertKeys" not in target
        assert "partition" not in target

    def test_upsert_without_keys_rejected(self, export_view):
        with pytest.raises(MammothValidationError) as exc:
            export_view.export.to_bigquery(
                selected_profile={},
                selected_identity={},
                table="t",
                export_type=BigQueryExportType.UPSERT,
            )
        assert exc.value.message == ERR_BIGQUERY_UPSERT_KEYS
        assert not export_view.export._captured


class TestToElasticsearch:
    def test_emits_exact_target(self, export_view):
        export_view.export.to_elasticsearch(
            host="es.local",
            username="u",
            password="p",
            index="idx",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.ELASTICSEARCH
        assert target == {
            "host": "es.local",
            "port": 9243,
            "username": "u",
            "password": "p",
            "index": "idx",
            "connection": "https",
            "chunksize": 200,
        }


# ── Cloud storage exports ─────────────────────────────────────


class TestToAzureBlob:
    def test_required_only(self, export_view):
        export_view.export.to_azure_blob(
            storage_account_name="acct",
            tenant_id="t",
            client_id="c",
            client_secret="s",
            container_name="cont",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.AZURE_BLOB
        assert target == {
            "storage_account_name": "acct",
            "tenant_id": "t",
            "client_id": "c",
            "client_secret": "s",
            "container_name": "cont",
        }

    def test_optional_path_and_file(self, export_view):
        export_view.export.to_azure_blob(
            storage_account_name="acct",
            tenant_id="t",
            client_id="c",
            client_secret="s",
            container_name="cont",
            folder_path="sub/dir",
            file_name="out.csv",
        )
        _, target, _ = export_view.export._captured[-1]
        assert target["folder_path"] == "sub/dir"
        assert target["file_name"] == "out.csv"


class TestToSharepoint:
    def test_emits_exact_target_with_default_library(self, export_view):
        export_view.export.to_sharepoint(
            tenant_id="t",
            client_id="c",
            client_secret="s",
            site_url="https://x.sharepoint.com/sites/s",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.SHAREPOINT
        assert target == {
            "tenant_id": "t",
            "client_id": "c",
            "client_secret": "s",
            "site_url": "https://x.sharepoint.com/sites/s",
            "document_library": "Documents",
        }


class TestToOnedrive:
    def test_emits_exact_target(self, export_view):
        export_view.export.to_onedrive(
            tenant_id="t",
            client_id="c",
            client_secret="s",
            user_id="user@x.com",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.ONEDRIVE
        assert target == {
            "tenant_id": "t",
            "client_id": "c",
            "client_secret": "s",
            "user_id": "user@x.com",
        }


# ── BI / publish exports ──────────────────────────────────────


class TestToTableau:
    def test_emits_exact_target_with_defaults(self, export_view):
        export_view.export.to_tableau(
            server_url="https://tableau.x.com",
            token_name="pat",
            token_secret="secret",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.TABLEAU_SERVER
        assert target == {
            "server_url": "https://tableau.x.com",
            "token_name": "pat",
            "token_secret": "secret",
            "site_name": "",
            "project_name": "Default",
            "datasource_name": "mammoth_export",
        }

    def test_ca_bundle_only_when_set(self, export_view):
        export_view.export.to_tableau(
            server_url="https://tableau.x.com",
            token_name="pat",
            token_secret="secret",
            ca_bundle_path="/etc/ssl/ca.pem",
        )
        _, target, _ = export_view.export._captured[-1]
        assert target["ca_bundle_path"] == "/etc/ssl/ca.pem"


class TestToPowerbi:
    def test_emits_camelcase_client_id(self, export_view):
        # Regression guard: backend reads the camelCase "clientId" key.
        export_view.export.to_powerbi(
            username="u",
            password="p",
            client_id="abc-123",
            dataset="ds",
            table="tbl",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.POWERBI
        assert target == {
            "username": "u",
            "password": "p",
            "clientId": "abc-123",
            "dataset": "ds",
            "table": "tbl",
        }
        assert "client_id" not in target


class TestToRestApi:
    def test_core_target_with_defaults(self, export_view):
        export_view.export.to_rest_api(
            base_url="https://api.x.com",
            endpoint_path="/v1/records",
        )
        handler, target, _ = export_view.export._captured[-1]
        assert handler is HandlerType.GENERIC_REST_API_EXPORT
        assert target == {
            "base_url": "https://api.x.com",
            "endpoint_path": "/v1/records",
            "auth_type": "none",
            "http_method": "POST",
            "wrap_path": "records",
            "batch_size": 1000,
            "timeout_seconds": 30,
            "ssl_verify": True,
        }

    def test_auth_merged_flat_and_optionals(self, export_view):
        export_view.export.to_rest_api(
            base_url="https://api.x.com",
            endpoint_path="/v1/records",
            auth_type=RestAuthType.BEARER,
            http_method=HttpMethod.PUT,
            auth={"token": "t0ken"},
            headers={"X-Env": "prod"},
            query_params={"v": "2"},
            extra_body_fields={"source": "mammoth"},
        )
        _, target, _ = export_view.export._captured[-1]
        # auth secrets are merged flat into the target, not nested.
        assert target["token"] == "t0ken"
        # Enums serialise to their wire string values.
        assert target["auth_type"] == "bearer"
        assert target["http_method"] == "PUT"
        assert target["default_headers"] == {"X-Env": "prod"}
        assert target["query_params"] == {"v": "2"}
        assert target["extra_body_fields"] == {"source": "mammoth"}

    @pytest.mark.parametrize("bad_batch", [0, -1, 10001])
    def test_rejects_out_of_range_batch_size(self, export_view, bad_batch):
        with pytest.raises(MammothValidationError) as exc:
            export_view.export.to_rest_api(
                base_url="https://api.x.com",
                endpoint_path="/v1/records",
                batch_size=bad_batch,
            )
        assert exc.value.message == ERR_REST_BATCH_SIZE.format(value=bad_batch)
        assert not export_view.export._captured  # never reached the API layer

    @pytest.mark.parametrize("bad_timeout", [4, 0, 301])
    def test_rejects_out_of_range_timeout(self, export_view, bad_timeout):
        with pytest.raises(MammothValidationError) as exc:
            export_view.export.to_rest_api(
                base_url="https://api.x.com",
                endpoint_path="/v1/records",
                timeout_seconds=bad_timeout,
            )
        assert exc.value.message == ERR_REST_TIMEOUT.format(value=bad_timeout)
        assert not export_view.export._captured

    @pytest.mark.parametrize("edge_batch", [1, 10000])
    def test_accepts_batch_size_bounds(self, export_view, edge_batch):
        # Inclusive bounds must pass.
        export_view.export.to_rest_api(
            base_url="https://api.x.com",
            endpoint_path="/v1/records",
            batch_size=edge_batch,
        )
        _, target, _ = export_view.export._captured[-1]
        assert target["batch_size"] == edge_batch


class TestPublishToDb:
    """publish_to_db bypasses _create_export — it POSTs to the dedicated
    publish-to-db endpoint with managed credentials, so assert the HTTP call
    shape directly."""

    def test_posts_to_publish_endpoint_with_odbc_body(self, export_view):
        export_view._client._request_json = MagicMock(return_value={"job_id": 7})
        result = export_view.export.publish_to_db(table="sales_dashboard")

        assert result == {"job_id": 7}
        export_view._client._request_json.assert_called_once()
        method, url = export_view._client._request_json.call_args[0][:2]
        body = export_view._client._request_json.call_args[1]["json"]
        assert method == "POST"
        assert url.endswith("/datasets/500/dataviews/1001/publish-to-db")
        # Managed creds server-side: body carries only odbc_type + table.
        assert body == {"odbc_type": "postgres", "target_properties": {"table": "sales_dashboard"}}

    def test_bigquery_odbc_type(self, export_view):
        export_view._client._request_json = MagicMock(return_value={"job_id": 8})
        export_view.export.publish_to_db(table="t", odbc_type=OdbcType.BIGQUERY)
        body = export_view._client._request_json.call_args[1]["json"]
        assert body["odbc_type"] == "bigquery"

    def test_requires_project_id(self, export_view):
        export_view._client.project_id = None
        with pytest.raises(ValueError, match="project_id"):
            export_view.export.publish_to_db(table="t")


# ── Dataset export ────────────────────────────────────────────


_RESOLVED_DS_ID = 4242


class TestToDataset:
    @staticmethod
    def _capture_run(view) -> dict[str, Any]:
        """Replace the internal-dataset export seam with a recorder.

        The seam returns the new dataset id (int); the recorder mimics that so
        callers' return value can be asserted.
        """
        captured: dict[str, Any] = {}

        def fake_run(target_properties, timeout=None, condition=None) -> int:
            captured["target_properties"] = target_properties
            captured["timeout"] = timeout
            captured["condition"] = condition
            return _RESOLVED_DS_ID

        view._run_internal_dataset_export = fake_run  # type: ignore[assignment]
        return captured

    def test_new_dataset_payload(self, export_view):
        captured = self._capture_run(export_view)
        new_id = export_view.export.to_dataset("New DS")
        assert new_id == _RESOLVED_DS_ID  # the resolved dataset id propagates out
        tp = captured["target_properties"]
        assert tp["DS_NAME"] == "New DS"
        assert tp["TARGET_DS_ID"] is None
        assert tp["SAVE_AS_DS_MODE"] == "REPLACE_IN_DS"
        assert tp["COLUMN_MAPPING"] == {}
        assert tp["TRANSFORM"] is None
        assert captured["condition"] is None

    def test_existing_dataset_append_with_mapping(self, export_view):
        captured = self._capture_run(export_view)
        mapping = {"col_a": "mapped_col"}
        export_view.export.to_dataset(
            "Existing DS",
            target_ds_id=42,
            save_as_mode=SaveAsDatasetMode.APPEND,
            column_mapping=mapping,
        )
        tp = captured["target_properties"]
        assert tp["TARGET_DS_ID"] == 42
        assert tp["SAVE_AS_DS_MODE"] == "APPEND_TO_DS"
        assert tp["COLUMN_MAPPING"] == mapping

    def test_condition_forwarded_to_seam_untouched(self, export_view):
        captured = self._capture_run(export_view)
        cond = Condition("col_a", Operator.EQ, "x")
        export_view.export.to_dataset("Filtered DS", condition=cond)
        # to_dataset forwards the TYPED condition object as-is — it does NOT
        # pre-build it (the seam owns building) and does NOT leak it into
        # target_properties (the filter is a top-level sibling).
        assert captured["condition"] is cond
        assert "CONDITION" not in captured["target_properties"]
        assert "TRANSFORM" in captured["target_properties"]

    def test_seam_builds_typed_condition_into_export_spec(self, export_view):
        # Exercise the REAL seam and capture the spec it builds, proving the
        # typed condition becomes the correct wire dict. target_ds_id is set so
        # the seam returns it directly (no new-dataset id resolution needed) —
        # this isolates the condition-building behaviour AND verifies the
        # existing-target id is returned.
        captured_spec: dict[str, Any] = {}

        def fake_create(dataview_id, export_spec, dataset_id):
            captured_spec["spec"] = export_spec
            return MagicMock()  # non-JobResponse → wait_for_job skipped

        export_view._client.exports = MagicMock()
        export_view._client.exports.create = fake_create

        new_id = export_view.export.to_dataset(
            "Filtered DS", target_ds_id=77, condition=Condition("col_a", Operator.EQ, "x")
        )
        assert new_id == 77  # existing-target id returned directly
        spec = captured_spec["spec"]
        # TEXT column + EQ is remapped to IN_LIST and keyed by the INTERNAL name.
        assert "column_aaa" in spec.condition
        assert "IN_LIST" in spec.condition["column_aaa"]
        # Branch-out carries no transform; the condition rides the spec, not it.
        assert spec.target_properties["TRANSFORM"] is None
        assert "CONDITION" not in spec.target_properties


class TestExportedDatasetIdResolution:
    """The seam resolves a NEW dataset's id from the executed export trigger."""

    @staticmethod
    def _export(ds_name, status, target_ds_id, export_id=1):
        e = MagicMock()
        e.id = export_id
        e.status = status
        e.target_properties = {"DS_NAME": ds_name, "TARGET_DS_ID": target_ds_id}
        return e

    def _page(self, exports):
        page = MagicMock()
        page.exports = exports
        return page

    def test_returns_id_of_executed_export_matching_name(self, export_view):
        # Two exports share the view; only the one named "Wanted" + EXECUTED counts.
        export_view._client.exports = MagicMock()
        export_view._client.exports.list.return_value = self._page(
            [
                self._export("Other", ExportStatus.EXECUTED, 111, export_id=1),
                self._export("Wanted", ExportStatus.EXECUTED, 222, export_id=2),
            ]
        )
        result = export_view._resolve_exported_dataset_id("Wanted", timeout=5)
        assert result == 222
        assert isinstance(result, int)

    def test_picks_most_recent_when_name_repeats(self, export_view):
        export_view._client.exports = MagicMock()
        export_view._client.exports.list.return_value = self._page(
            [
                self._export("Dup", ExportStatus.EXECUTED, 100, export_id=5),
                self._export("Dup", ExportStatus.EXECUTED, 200, export_id=9),  # newest
            ]
        )
        assert export_view._resolve_exported_dataset_id("Dup", timeout=5) == 200

    def test_times_out_if_never_executed(self, export_view):
        # Export exists but stays un-executed → must raise, not hang or lie.
        export_view._client.exports = MagicMock()
        export_view._client.exports.list.return_value = self._page(
            [self._export("Pending", ExportStatus.EXECUTING, None, export_id=1)]
        )
        with patch("mammoth.view.time") as fake_time:
            # monotonic advances past the deadline on the 2nd check; sleep is a no-op.
            fake_time.monotonic.side_effect = [0.0, 0.5, 99.0]
            fake_time.sleep.return_value = None
            with pytest.raises(MammothExportError) as exc:
                export_view._resolve_exported_dataset_id("Pending", timeout=1)
        assert exc.value.details["dataset_name"] == "Pending"


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
