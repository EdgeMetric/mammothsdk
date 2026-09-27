"""``_execute`` adds the ``verify`` read-back to real, non-read, API-backed writes.

See :mod:`mammoth_cli.runtime.verify` for the pure derivation, and
``mammoth_cli.commands.view_ops._dispatch_view`` for the ``row_check`` a plain
view transform gets when it declares no ``before``/``after`` of its own.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import view_ops as view_ops_cmd
from mammoth_cli.runtime.invocation import Invocation, ResourceRef
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DELETE = "mammoth.api.datasets.DatasetsAPI.delete"
_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_JSON_NO_INPUT = ["--output", "json", "--no-input"]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _parent(view_id: int) -> ResourceRef:
    return ResourceRef(dataset_id=122, view_id=view_id)


def _write(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


def test_a_mutating_command_gets_a_verify_block(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DELETE] = {"status": "done"}
    result = make_runner().invoke(
        ["dataset", "delete", "7", "--project", "180", "--yes", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["verify"] == {
        "verified": True,
        "state": "done",
        "warnings": [],
        "needs_user": None,
    }


def test_a_read_command_gets_no_verify_block(fake_service: FakeMammothService) -> None:
    result = make_runner().invoke(["dataset", "get", "7", "--project", "180", *_JSON_NO_INPUT])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert "verify" not in data


def test_a_dry_run_gets_no_verify_block(fake_service: FakeMammothService) -> None:
    result = make_runner().invoke(
        ["dataset", "delete", "7", "--project", "180", "--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert "verify" not in data


def test_a_plain_view_transform_gets_a_row_check(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
        )
    )
    assert data["row_check"] == {"rows_before": 20, "rows_after": 20}
    assert (
        fake_service.call_log.count(
            (_DATAVIEW_GET, {"dataset_id": 122, "dataview_id": 3, "project_id": None})
        )
        == 2
    )


def test_a_join_transform_keeps_its_own_join_check_not_row_check(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}
    doc = {
        "foreign_view": 9,
        "join_type": "OUTER",
        "on": [{"left": "a", "right": "a"}],
        "select": [{"column": "b"}],
    }
    data, _meta = view_ops_cmd.view_transform_join(
        _inv(
            "view.transform.join",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, doc),
        )
    )
    assert "row_check" not in data
    assert "join_check" in data
