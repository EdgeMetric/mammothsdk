"""``--output yaml`` carries what ``--output json`` carries, for every envelope data shape."""

from __future__ import annotations

import io
import json

import pytest
import yaml

from mammoth_cli.commands.schema import get_schema
from mammoth_cli.output.normalize import DataRows, Revealed
from mammoth_cli.output.render import render


def _both(envelope: dict) -> tuple[dict, dict]:
    as_yaml, as_json = io.StringIO(), io.StringIO()
    render(envelope, output="yaml", stream=as_yaml)
    render(envelope, output="json", stream=as_json)
    return yaml.safe_load(as_yaml.getvalue()), json.loads(as_json.getvalue())


@pytest.mark.parametrize(
    "data",
    [
        DataRows([{"a": 1}, {"a": 2}]),
        Revealed({"token": "mm_abc"}),
        get_schema("project.list"),
        {"nested": DataRows([{"b": [1, 2]}])},
        {1: "int key", "b": 2},
        {"nan": float("nan")},
    ],
    ids=["data-rows", "revealed", "schema-document", "nested-rows", "int-key", "nan"],
)
def test_yaml_equals_json_for_every_data_shape(data: object) -> None:
    from_yaml, from_json = _both({"ok": True, "data": data})
    assert from_yaml == from_json
