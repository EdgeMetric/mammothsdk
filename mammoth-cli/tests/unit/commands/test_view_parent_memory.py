"""A parent seen once (``view list``, ``view get``) serves every later mutation."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.commands import view_ops as view_ops_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_VIEW_LIST = "mammoth.api.dataviews.DataviewsAPI.list"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_transform_without_a_known_parent_still_fails_closed(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text('{"name": "Col"}', encoding="utf-8")
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_add_column(
            _inv("view.transform.add-column", extra_args=["45"], input_file=str(doc))
        )
    assert excinfo.value.code == "missing_argument"
    assert fake_service.view_call_log == []


def test_view_list_teaches_the_parent_to_later_transforms(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_VIEW_LIST] = {
        "dataviews": [{"id": 45, "dataset_id": 122, "name": "v1"}, {"id": 46, "dataset_id": 122}]
    }
    view_cmd.view_list(_inv("view.list", project=180, extra_args=["122"]))
    assert parents.lookup("default", 4, 45) == 122
    assert parents.lookup("default", 4, 46) == 122

    doc = tmp_path / "in.json"
    doc.write_text('{"name": "Col"}', encoding="utf-8")
    view_ops_cmd.view_transform_add_column(
        _inv("view.transform.add-column", extra_args=["45"], input_file=str(doc))
    )
    assert fake_service.view_call_log == [(45, "add_column", {"dataset_id": 122, "name": "Col"})]


def test_explicit_parent_wins_over_memory(fake_service: FakeMammothService, tmp_path: Path) -> None:
    parents.remember("default", 4, {45: 122})
    doc = tmp_path / "in.json"
    doc.write_text('{"name": "Col", "dataset_id": 130}', encoding="utf-8")
    view_ops_cmd.view_transform_add_column(
        _inv("view.transform.add-column", extra_args=["45"], input_file=str(doc))
    )
    assert fake_service.view_call_log[-1][2]["dataset_id"] == 130


def test_memory_is_scoped_by_profile_and_workspace() -> None:
    parents.remember("release", 4, {45: 122})
    assert parents.lookup("release", 4, 45) == 122
    assert parents.lookup("app", 4, 45) is None
    assert parents.lookup("release", 5, 45) is None


def test_remember_records_ignores_non_view_shapes() -> None:
    parents.remember_records("default", 1, {"id": 9, "name": "no dataset here"})
    parents.remember_records("default", 1, [{"id": "x", "dataset_id": 3}])
    assert parents.lookup("default", 1, 9) is None
