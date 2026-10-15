"""Wiring: a dataset's health entry reaches what a real command returns.

The check itself is covered in ``tests/unit/runtime/test_dataset_health.py``.
"""

from __future__ import annotations

import json

from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner


def test_a_real_dataset_read_carries_the_health_entry(
    isolated_cli_config: object, fake_service: FakeMammothService
) -> None:
    """Wiring: the check runs on what a command actually returns, not only when
    called directly."""
    login_default_profile()
    fake_service.responses["mammoth.api.datasets.DatasetsAPI.get"] = {
        "id": 2759,
        "name": "book3.csv",
        "status": "has_unstructured_data",
    }

    result = make_runner().invoke(
        ["dataset", "get", "2759", "--project", "180", "--output", "json", "--no-input"]
    )

    assert result.exit_code == 0, result.output
    health = json.loads(result.output)["data"]["dataset_health"]
    assert [h["dataset_id"] for h in health] == [2759]


def test_a_real_dataset_read_says_how_new_data_arrives(
    isolated_cli_config: object, fake_service: FakeMammothService
) -> None:
    """Wiring: the next-file path reaches what ``dataset get`` returns."""
    login_default_profile()
    fake_service.responses["mammoth.api.datasets.DatasetsAPI.get"] = {
        "id": 2830,
        "name": "brand_campaigns.csv",
        "status": "ready",
        "sources": [{"type": "file"}],
    }

    result = make_runner().invoke(
        ["dataset", "get", "2830", "--project", "180", "--output", "json", "--no-input"]
    )

    assert result.exit_code == 0, result.output
    paths = json.loads(result.output)["data"]["new_data"]
    assert [p["dataset_id"] for p in paths] == [2830]


def test_dataset_list_reports_a_real_health_for_each_dataset(
    isolated_cli_config: object, fake_service: FakeMammothService
) -> None:
    """Bug bash 2026-10-15: every row of ``dataset list`` said ``unknown`` because the
    compact summary dropped the ``ready`` status the list route does return."""
    login_default_profile()
    fake_service.responses["mammoth.api.datasets.DatasetsAPI.list"] = {
        "datasets": [
            {"id": 313554, "name": "foo.csv 4", "status": "ready", "sources": [{"type": "file"}]},
            {"id": 313551, "name": "bar.csv", "status": "has_unstructured_data"},
        ]
    }

    result = make_runner().invoke(
        ["dataset", "list", "--project", "2091", "--output", "json", "--no-input"]
    )

    assert result.exit_code == 0, result.output
    health = {h["dataset_id"]: h for h in json.loads(result.output)["data"]["dataset_health"]}
    assert health[313554]["health"] == "healthy"
    assert health[313554]["name"] == "foo.csv 4"
    assert health[313551]["health"] == "unhealthy"
    assert "unknown" not in {h["health"] for h in health.values()}
