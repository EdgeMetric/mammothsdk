"""Deterministic SDK documentation inventory and safe snippet checks."""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

from mammoth import MammothClient, parse_path
from mammoth.api.files import FilesAPI
from mammoth.client import ViewsResource

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sdk_docs_inventory.py"


def _inventory_module():
    spec = importlib.util.spec_from_file_location("sdk_docs_inventory", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sdk_docs_inventory_is_deterministic_and_reports_gaps() -> None:
    module = _inventory_module()
    first = module.inventory()
    second = module.inventory()

    assert first == second
    assert first["denominator"] == len(first["entries"])
    assert first["documented"] + first["gaps"] == first["denominator"]
    assert first["gaps"] > 0  # This tool reports, rather than hides, coverage gaps.
    assert any(entry["gap"] == "no_docs_anchor" for entry in first["entries"])
    assert any(
        entry["symbol"] == "mammoth.api.datasets.DatasetsAPI.list"
        and entry["docs_anchor"] == "api/datasets.md#full-api-reference"
        for entry in first["entries"]
    )


def test_basic_usage_snippets_match_current_signatures_without_network() -> None:
    """Execute the safe setup/URL examples and bind the documented API calls."""
    assert parse_path("https://app.mammoth.io/#/workspaces/11/projects/10/views/1039") == {
        "workspace_id": 11,
        "project_id": 10,
        "dataview_id": 1039,
    }

    with patch("mammoth.client.requests.Session") as session_factory:
        session_factory.return_value.headers = MagicMock()
        with MammothClient("key", "secret", workspace_id=11) as client:
            client.set_project_id(10)
            assert client.project_id == 10
        session_factory.return_value.close.assert_called_once()

    inspect.signature(ViewsResource.list).bind(None, dataset_id=42)
    inspect.signature(FilesAPI.upload).bind(None, "sales.csv")
