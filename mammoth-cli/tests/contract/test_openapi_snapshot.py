"""Red-first snapshot and inventory tests.

These validate the pinned OpenAPI snapshot and its generated inventory without
network access. CI must never fetch the live document.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

CLI_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOT = CLI_ROOT / "spec" / "openapi" / "openapi.json"
METADATA = CLI_ROOT / "spec" / "openapi" / "metadata.json"

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def _load_snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def _count_operations(document: dict) -> int:
    return sum(
        1
        for item in document.get("paths", {}).values()
        for method in item
        if method.lower() in HTTP_METHODS
    )


def test_openapi_snapshot_metadata() -> None:
    assert METADATA.exists(), "pinned metadata missing"
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    document = _load_snapshot()
    assert metadata["openapi_version"] == "3.1.0"
    assert metadata["path_count"] == len(document["paths"])
    assert metadata["operation_count"] == _count_operations(document)
    assert metadata["source_url"].endswith("/api/v2/docs/openapi.json")


def test_openapi_inventory_digest_matches_snapshot() -> None:
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
    assert metadata["sha256"] == digest, "metadata digest does not match pinned snapshot"


def test_openapi_inventory_is_nonempty() -> None:
    document = _load_snapshot()
    assert _count_operations(document) > 0


def test_openapi_inventory_identity_is_method_and_path() -> None:
    from mammoth_cli.manifest.loader import load_operations

    operations = load_operations()
    assert operations, "operation manifest is empty"
    assert len(operations) == _count_operations(_load_snapshot())
    seen: set[str] = set()
    for record in operations:
        expected = f"{record['method']} {record['path']}"
        assert record["identity"] == expected
        assert record["identity"] not in seen, f"duplicate identity {record['identity']}"
        seen.add(record["identity"])


def test_live_drift_comparison_detects_inventory_and_schema_changes(monkeypatch, capsys) -> None:
    """Exercise the opt-in network check without making the test network-dependent."""
    scripts = CLI_ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        import sync_openapi

        committed = _load_snapshot()
        monkeypatch.setattr(sync_openapi, "fetch_document", lambda: (b"", committed))
        assert sync_openapi.check_live() == 0

        changed = json.loads(json.dumps(committed))
        changed["paths"]["/__inventory_drift_test__"] = {
            "get": {"operationId": "InventoryDriftTest"}
        }
        monkeypatch.setattr(sync_openapi, "fetch_document", lambda: (b"", changed))
        assert sync_openapi.check_live() == 1
        assert "+ GET /__inventory_drift_test__" in capsys.readouterr().err

        changed = json.loads(json.dumps(committed))
        schema = next(iter(changed["components"]["schemas"].values()))
        schema["__contract_drift_test__"] = {"type": "string"}
        monkeypatch.setattr(sync_openapi, "fetch_document", lambda: (b"", changed))
        assert sync_openapi.check_live() == 1
        assert "component schema changed" in capsys.readouterr().err

        documentation_only = json.loads(json.dumps(committed))
        documentation_only["info"]["description"] = "non-contract wording changed"
        documentation_only["components"]["schemas"]["ProjectProperties"]["properties"]["color"][
            "default"
        ] = "#000000"
        monkeypatch.setattr(sync_openapi, "fetch_document", lambda: (b"", documentation_only))
        assert sync_openapi.check_live() == 0
    finally:
        sys.path.remove(str(scripts))


def test_generated_dashboard_wrappers_have_no_drift() -> None:
    scripts = CLI_ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        import gen_dashboard_v3_sdk

        assert (
            gen_dashboard_v3_sdk.OUTPUT.read_text(encoding="utf-8") == gen_dashboard_v3_sdk.build()
        )
        assert (
            gen_dashboard_v3_sdk.MODELS_OUTPUT.read_text(encoding="utf-8")
            == gen_dashboard_v3_sdk.build_models()
        )
    finally:
        sys.path.remove(str(scripts))


def test_generated_dashboard_wrapper_routes_path_query_and_body() -> None:
    from mammoth.api import dashboard_generated as generated

    calls: list[tuple] = []

    class Client:
        def _request_json(self, *args, **kwargs):
            calls.append((args, kwargs))
            return {"column": "region", "total": 1, "values": ["west"]}

    owner = type("Owner", (), {"_client": Client()})()
    response = generated.rls_value_list(owner, 17, "region", "west")
    assert response.model_dump() == {"column": "region", "total": 1, "values": ["west"]}
    assert calls == [
        (("GET", "/dashboards/17/rls/values"), {"params": {"column": "region", "search": "west"}})
    ]


def test_generated_nullable_parameter_types_and_routing() -> None:
    from mammoth.api import dashboard_generated as generated

    scripts = CLI_ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        import gen_dashboard_v3_sdk

        assert (
            gen_dashboard_v3_sdk.schema_annotation(
                {"oneOf": [{"type": "integer"}, {"type": "null"}]}
            )
            == "int | None"
        )
        assert (
            gen_dashboard_v3_sdk.schema_annotation({"type": "array", "items": {"type": "boolean"}})
            == "list[bool]"
        )
        project_parameter = next(
            parameter
            for parameter in _load_snapshot()["paths"]["/dashboards"]["get"]["parameters"]
            if parameter["name"] == "project_id"
        )
        assert gen_dashboard_v3_sdk.schema_annotation(project_parameter["schema"]) == "int | None"
    finally:
        sys.path.remove(str(scripts))

    signature = inspect.signature(generated.chat_history)
    assert signature.parameters["sequence"].annotation == "int | None"

    calls: list[tuple] = []

    class Client:
        def _request_json(self, *args, **kwargs):
            calls.append((args, kwargs))
            if args[1].endswith("/chat"):
                return {"sequence": 3}
            return {"dataview_id": 42}

    owner = type("Owner", (), {"_client": Client()})()
    generated.chat_history(owner, 17, sequence=3)
    generated.template_fit(owner, 42, table_item_id=9)
    assert calls[0][1]["params"] == {"sequence": 3}
    assert calls[1][1]["params"] == {"dataview_id": 42, "table_item_id": 9}


def test_generated_dashboard_named_bodies_and_results_are_typed() -> None:
    from mammoth.api import dashboard_generated as generated

    signature = inspect.signature(generated.v3_generate)
    assert signature.parameters["body"].annotation == "GenerateDashboardV3Spec"
    assert signature.return_annotation == "ObjectJobSchema | JobResponse"

    owner = type(
        "Owner",
        (),
        {"_client": type("Client", (), {"_request_json": lambda *_a, **_kw: {"job_id": 9}})()},
    )()
    result = generated.v3_generate(
        owner, {"params": {"dataview_id": 1, "intent": "Revenue by quarter"}}
    )
    assert type(result).__name__ == "ObjectJobSchema"
    assert result.job_id == 9

    invalid_owner = type(
        "Owner",
        (),
        {"_client": type("Client", (), {"_request_json": lambda *_a, **_kw: {"oops": 9}})()},
    )()
    with pytest.raises(ValidationError):
        generated.v3_generate(
            invalid_owner, {"params": {"dataview_id": 1, "intent": "Revenue by quarter"}}
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
