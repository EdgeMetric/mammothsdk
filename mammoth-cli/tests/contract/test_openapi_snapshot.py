"""Red-first snapshot and inventory tests.

These validate the pinned OpenAPI snapshot and its generated inventory without
network access. CI must never fetch the live document.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

CLI_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOT = CLI_ROOT / "spec" / "openapi" / "openapi.json"
METADATA = CLI_ROOT / "spec" / "openapi" / "metadata.json"

EXPECTED_PATH_COUNT = 234
EXPECTED_OPERATION_COUNT = 376
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
    assert metadata["openapi_version"] == "3.1.0"
    assert metadata["path_count"] == EXPECTED_PATH_COUNT
    assert metadata["operation_count"] == EXPECTED_OPERATION_COUNT
    assert metadata["source_url"].endswith("/api/v2/docs/openapi.json")


def test_openapi_inventory_digest_matches_snapshot() -> None:
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
    assert metadata["sha256"] == digest, "metadata digest does not match pinned snapshot"


def test_openapi_inventory_has_376_operations() -> None:
    document = _load_snapshot()
    assert _count_operations(document) == EXPECTED_OPERATION_COUNT


def test_openapi_inventory_identity_is_method_and_path() -> None:
    from mammoth_cli.manifest.loader import load_operations

    operations = load_operations()
    assert operations, "operation manifest is empty"
    assert len(operations) == EXPECTED_OPERATION_COUNT
    seen: set[str] = set()
    for record in operations:
        expected = f"{record['method']} {record['path']}"
        assert record["identity"] == expected
        assert record["identity"] not in seen, f"duplicate identity {record['identity']}"
        seen.add(record["identity"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
