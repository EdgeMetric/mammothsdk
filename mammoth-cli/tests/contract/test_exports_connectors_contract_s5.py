"""Independent C2/S5 checks for export, connector, key, and webhook routes.

The route ledger is deliberately separate from the shared contract resolver.
These tests run the public SDK and its request construction against a recording
transport, so the expected method/path/body assertions do not come from the
CLI resolver or the service fake.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mammoth_cli.commands import connector as connector_cmd
from mammoth_cli.commands import external_key as external_key_cmd
from mammoth_cli.commands import view as view_cmd
from mammoth_cli.commands import webhook as webhook_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.runtime.invocation import Invocation

LEDGER = Path(__file__).with_name("fixtures") / "C2-S5-ROUTES.json"
S5_PREFIXES = ("view.export", "connector", "external-key", "webhook")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, Any]) -> str:
    path = tmp_path / "s5-input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _patch_service(
    monkeypatch: pytest.MonkeyPatch,
    service: Any,
    modules: tuple[Any, ...],
    *,
    workspace_id: int = 4,
) -> None:
    class _Context:
        def __enter__(self) -> tuple[Any, Any]:
            return service, SimpleNamespace(workspace_id=workspace_id)

        def __exit__(self, *_args: object) -> None:
            return None

    def context(_invocation: Invocation) -> _Context:
        return _Context()

    for module in modules:
        monkeypatch.setattr(module, "open_service", context)


def _ledger() -> dict[str, Any]:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_s5_ledger_covers_exact_manifest_surface() -> None:
    ledger = _ledger()
    routes = ledger["routes"]
    expected = sorted(
        record["command_id"]
        for record in load_commands()
        if record["command_id"].startswith(S5_PREFIXES)
    )
    assert ledger["route_count"] == 60
    assert sorted(route["command_id"] for route in routes) == expected
    for route in routes:
        record = command_by_id(route["command_id"])
        assert record is not None
        assert route["sdk_symbol"] == record["sdk_symbol"]
        assert isinstance(route["field_destinations"], dict)
        assert route["wire"]["method"] in {"GET", "POST", "PATCH", "PUT", "DELETE"}
        assert route["wire"]["path"].startswith("/")
        assert route["wire_verification"]["status"] in {"verified", "unverified"}
        assert route["dropped_field_sentinel"] == "__s5_dropped_field__"


def test_postgres_export_executes_exact_scoped_wire(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=180)
    api.default(200, {"trigger_id": 71})
    api.on("GET", r"/dataviews/7$", body={"id": 7, "metadata": []})
    _patch_service(monkeypatch, service, (view_cmd,))

    view_cmd.view_export_specialized(
        _inv(
            "view.export.postgres",
            project=180,
            extra_args=["7", "9"],
            input_file=_write(
                tmp_path,
                {
                    "host": "db.example",
                    "port": 5432,
                    "database": "analytics",
                    "table": "exports",
                    "username": "agent",
                    "password": "secret-sentinel",
                    "run_immediately": False,
                    "validate_only": True,
                },
            ),
            yes=True,
        )
    )

    request = api.last()
    assert request.method == "POST"
    assert request.path == (
        "/api/v2/workspaces/4/projects/180/datasets/9/dataviews/7/pipeline/exports"
    )
    assert request.json_body["DATAVIEW_ID"] == 7
    assert request.json_body["handler_type"] == "postgres"
    assert request.json_body["target_properties"] == {
        "host": "db.example",
        "port": 5432,
        "database": "analytics",
        "table": "exports",
        "username": "agent",
        "password": "secret-sentinel",
    }
    assert request.json_body["run_immediately"] is False
    assert request.json_body["validate_only"] is True


def test_rest_export_preserves_distinct_target_and_optional_wire_fields(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=180)
    api.default(200, {"trigger_id": 72})
    api.on("GET", r"/dataviews/8$", body={"id": 8, "metadata": []})
    _patch_service(monkeypatch, service, (view_cmd,))

    view_cmd.view_export_specialized(
        _inv(
            "view.export.rest",
            project=180,
            extra_args=["8", "10"],
            input_file=_write(
                tmp_path,
                {
                    "base_url": "https://sink.example",
                    "endpoint_path": "/v2/records",
                    "http_method": "PUT",
                    "auth_type": "bearer",
                    "auth": {"token": "secret-sentinel"},
                    "headers": {"X-S5": "distinct"},
                    "query_params": {"source": "s5"},
                    "extra_body_fields": {"marker": 73},
                    "batch_size": 17,
                },
            ),
            yes=True,
        )
    )

    request = api.last()
    assert request.method == "POST"
    assert request.path == (
        "/api/v2/workspaces/4/projects/180/datasets/10/dataviews/8/pipeline/exports"
    )
    target = request.json_body["target_properties"]
    assert target == {
        "base_url": "https://sink.example",
        "endpoint_path": "/v2/records",
        "auth_type": "bearer",
        "http_method": "PUT",
        "wrap_path": "records",
        "batch_size": 17,
        "timeout_seconds": 30,
        "ssl_verify": True,
        "token": "secret-sentinel",
        "default_headers": {"X-S5": "distinct"},
        "query_params": {"source": "s5"},
        "extra_body_fields": {"marker": 73},
    }


def test_connector_ds_config_executes_exact_body(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=180)
    api.default(200, {})
    _patch_service(monkeypatch, service, (connector_cmd,))

    connector_cmd.connector_ds_config_create(
        _inv(
            "connector.ds-config.create",
            project=180,
            extra_args=["postgres", "warehouse"],
            input_file=_write(
                tmp_path,
                {
                    "query": "SELECT sentinel_value",
                    "table": "orders",
                    "profile": "analytics",
                    "validate": False,
                    "data_sample": True,
                },
            ),
            yes=True,
        )
    )

    request = api.last()
    assert request.method == "POST"
    assert request.path == (
        "/api/v2/workspaces/4/projects/180/connectors/postgres/connections/warehouse/ds_configs"
    )
    assert request.json_body == {
        "query": "SELECT sentinel_value",
        "table": "orders",
        "profile": "analytics",
        "validate": False,
        "data_sample": True,
    }


def test_external_key_secret_is_input_only_and_wire_is_exact(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    api.default(200, {})
    _patch_service(monkeypatch, service, (external_key_cmd,))

    external_key_cmd.external_key_create(
        _inv(
            "external-key.create",
            input_file=_write(
                tmp_path,
                {
                    "key_type": "anthropic",
                    "key_name": "sentinel-key",
                    "secure_key": "secret-sentinel",
                    "description": "for contract test",
                },
            ),
            yes=True,
            confirm="4",
        )
    )

    request = api.last()
    assert request.method == "POST"
    assert request.path == "/api/v2/workspaces/4/external_keys"
    assert request.json_body == {
        "key_type": "anthropic",
        "key_name": "sentinel-key",
        "secure_key": "secret-sentinel",
        "description": "for contract test",
    }


def test_webhook_update_executes_patch_wire_and_empty_patch_is_rejected(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=180)
    api.default(200, {})
    _patch_service(monkeypatch, service, (webhook_cmd,))

    webhook_cmd.webhook_update(
        _inv(
            "webhook.update",
            project=180,
            extra_args=[23],
            input_file=_write(tmp_path, {"mode": "combine", "is_secure": False}),
        )
    )
    request = api.last()
    assert request.method == "PATCH"
    assert request.path == "/api/v2/workspaces/4/projects/180/webhooks/23"
    assert request.json_body == {
        "patch": [
            {"op": "replace", "path": "mode", "value": "combine"},
            {"op": "replace", "path": "is_secure", "value": False},
        ]
    }

    before = len(api.requests)
    with pytest.raises(CliError) as error:
        webhook_cmd.webhook_update(_inv("webhook.update", project=180, extra_args=[23]))
    assert error.value.code == "missing_field"
    assert len(api.requests) == before


def test_unknown_s5_field_is_rejected_before_any_wire(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=180)
    _patch_service(monkeypatch, service, (view_cmd,))
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.email",
                project=180,
                extra_args=[7, 9],
                input_file=_write(
                    tmp_path,
                    {"emails": ["recipient@example.com"], "__s5_dropped_field__": "sentinel"},
                ),
                yes=True,
            )
        )
    assert error.value.code == "unknown_input_field"
    assert api.requests == []
