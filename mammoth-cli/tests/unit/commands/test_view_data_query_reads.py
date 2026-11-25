"""``view data query` reads the view and its dataset once per command (mammothsdk#400)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_DATA_QUERY = "mammoth.api.dataviews.DataviewsAPI.query_data"
_VIEW = {
    "metadata": [
        {"internal_name": "column_1", "display_name": "a", "type": "TEXT"},
        {"internal_name": "column_2", "display_name": "b", "type": "NUMERIC"},
    ]
}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _count(fake_service: FakeMammothService, symbol: str) -> int:
    return sum(1 for name, _kwargs in fake_service.call_log if name == symbol)


def test_a_query_with_a_filter_and_rows_reads_the_view_and_dataset_once(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = _VIEW
    fake_service.responses[_DATA_QUERY] = {"data": [{"column_1": "x", "column_2": 5}]}
    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps(
            {"columns": ["a", "b"], "condition": {"column": "b", "operator": ">", "value": 3}}
        ),
        encoding="utf-8",
    )
    data, _meta = view_cmd.view_data_query(
        Invocation(
            command_id="view.data.query",
            project=180,
            extra_args=["7", "9"],
            input_file=str(doc),
        )
    )
    assert data["data"] == [{"a": "x", "b": 5}]  # relabelled from the one read
    assert _count(fake_service, _DATAVIEW_GET) == 1
    assert _count(fake_service, _DATASET_GET) == 1
    assert _count(fake_service, _DATA_QUERY) == 1


def test_a_plain_query_with_rows_reads_the_view_once(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DATAVIEW_GET] = _VIEW
    fake_service.responses[_DATA_QUERY] = {"data": [{"column_1": "x", "column_2": 5}]}
    data, _meta = view_cmd.view_data_query(
        Invocation(command_id="view.data.query", project=180, extra_args=["7", "9"])
    )
    assert data["data"] == [{"a": "x", "b": 5}]
    assert _count(fake_service, _DATAVIEW_GET) == 1
    assert _count(fake_service, _DATASET_GET) == 1
