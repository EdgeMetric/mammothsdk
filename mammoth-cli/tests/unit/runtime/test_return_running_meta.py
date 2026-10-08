"""``--return-running`` keeps the meta a read handler computed before its job ran out."""

from __future__ import annotations

import json

import pytest
from mammoth.exceptions import MammothJobTimeoutError

from mammoth_cli.runtime.executor import run
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.mapping import map_sdk_exception


def test_running_envelope_keeps_dataset_and_view_meta(capsys: pytest.CaptureFixture[str]) -> None:
    invocation = Invocation(command_id="view.data.aggregate", output="json", return_running=True)

    def handler() -> tuple[object, dict[str, object]]:
        meta = {
            "profile": "default",
            "dataset": {"id": 1, "name": "Sales", "row_count": 10},
            "view": {"id": 2, "name": "View 1", "row_count": 4},
        }
        object.__setattr__(invocation, "read_meta", meta)
        exc = MammothJobTimeoutError(
            27102, 20, observed_job={"operation": "get_volatile_query_data"}
        )
        raise map_sdk_exception(exc)

    run("view.data.aggregate", "json", handler, profile="default", invocation=invocation)

    envelope = json.loads(capsys.readouterr().out)
    assert envelope["data"]["status"] == "running"
    assert envelope["meta"]["view"]["name"] == "View 1"
    assert envelope["meta"]["dataset"]["name"] == "Sales"
    assert envelope["meta"]["profile"] == "default"
