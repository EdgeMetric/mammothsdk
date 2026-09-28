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
