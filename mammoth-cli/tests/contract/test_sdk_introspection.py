"""SDK inventory introspection tests.

These assert the committed SDK manifest matches live introspection so the parity
record cannot silently drift from the SDK source.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

CLI_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = CLI_ROOT / "scripts"
MANIFESTS = CLI_ROOT / "spec" / "manifests"

EXPECTED_METHOD_COUNT = 471


def _introspection() -> dict:
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import inventory_sdk

    return inventory_sdk.build_document()


def test_sdk_inventory_matches_public_surface() -> None:
    document = _introspection()
    assert document["method_count"] == EXPECTED_METHOD_COUNT
    live = {record["sdk_symbol"] for record in document["methods"]}
    manifest = {
        record["sdk_symbol"]
        for record in yaml.safe_load((MANIFESTS / "sdk-methods.yaml").read_text())["methods"]
    }
    assert manifest == live, "sdk manifest and introspection disagree"


def test_sdk_manifest_signatures_and_defaults_match_introspection() -> None:
    live = {record["sdk_symbol"]: record["signature"] for record in _introspection()["methods"]}
    manifest = yaml.safe_load((MANIFESTS / "sdk-methods.yaml").read_text())["methods"]
    for record in manifest:
        assert record["signature"] == live[record["sdk_symbol"]], record["sdk_symbol"]
