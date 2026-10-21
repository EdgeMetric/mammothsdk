"""``View.set_column_format`` sends the FORMAT_INFO patch the backend's DisplayPropertiesUpdate reads."""

from __future__ import annotations

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothColumnError, MammothValidationError
from mammoth.view import View
from tests.unit._loopback import RecordingServer, client, server  # noqa: F401

VIEW_PATH = "/workspaces/1/projects/25654/datasets/500/dataviews/42"
METADATA = [
    {"internal_name": "column_1", "display_name": "Admitted", "type": "DATE"},
    {"internal_name": "column_2", "display_name": "Revenue", "type": "NUMERIC"},
]


def _view_record(format_info: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        "id": 42,
        "name": "V",
        "metadata": METADATA,
        "display_properties": {"FORMAT_INFO": format_info},
    }


async def _view(client: MammothClient, server: RecordingServer, info: dict) -> View:  # noqa: F811
    server.answers[f"GET {VIEW_PATH}"] = _view_record(info)
    return View(client, _view_record(info), 500)


async def test_it_patches_format_info_by_internal_name_and_keeps_the_other_keys(
    client: MammothClient, server: RecordingServer  # noqa: F811
) -> None:
    current = {"column_2": {"currency_symbol": "$", "decimal_spec": 0}}
    view = await _view(client, server, current)
    after = {"column_2": {"currency_symbol": "$", "decimal_spec": 2}}
    server.answers[f"GET {VIEW_PATH}"] = _view_record(after)

    result = await view.set_column_format({"Revenue": {"decimal_spec": 2}})

    patches = [r for r in server.requests if r["method"] == "PATCH"]
    assert len(patches) == 1
    assert patches[0]["path"] == VIEW_PATH
    assert patches[0]["body"] == {
        "patch": [
            {
                "op": "replace",
                "path": "display_properties/FORMAT_INFO",
                "value": {"column_2": {"currency_symbol": "$", "decimal_spec": 2}},
            }
        ]
    }
    assert result == {"formatted": {"Revenue": after["column_2"]}}


async def test_a_key_that_is_not_a_format_key_is_refused_before_any_request(
    client: MammothClient, server: RecordingServer  # noqa: F811
) -> None:
    view = await _view(client, server, {})
    with pytest.raises(MammothValidationError, match="unknown: date_fmt"):
        await view.set_column_format({"Admitted": {"date_fmt": "%d"}})
    assert server.requests == []


async def test_an_unknown_column_is_refused_before_any_request(
    client: MammothClient, server: RecordingServer  # noqa: F811
) -> None:
    view = await _view(client, server, {})
    with pytest.raises(MammothColumnError):
        await view.set_column_format({"Nope": {"date_format": "%d"}})
    assert server.requests == []
