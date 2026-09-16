"""CLI-handler checks for scoped transform resource context."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import view_ops
from mammoth_cli.runtime.invocation import Invocation, ResourceRef
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Provide the same disposable profile used by other command tests."""
    login_default_profile()


def _write(path: Path, payload: dict[str, object]) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_transform_input_dataset_id_reaches_view_service(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(
        tmp_path / "request.json",
        {"dataset_id": 55, "expression": "Price * Qty", "new_column": "Total"},
    )

    view_ops.view_transform_math(
        Invocation(
            command_id="view.transform.math",
            extra_args=["1039"],
            input_file=input_file,
        )
    )

    assert fake_service.view_call_log == [
        (
            1039,
            "math",
            {"dataset_id": 55, "expression": "Price * Qty", "new_column": "Total"},
        )
    ]


def test_typed_resource_reference_reaches_view_service(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write(tmp_path / "request.json", {"expression": "Price * Qty"})
    view_ops.view_transform_math(
        Invocation(
            command_id="view.transform.math",
            extra_args=["1039"],
            resource_ref=ResourceRef(workspace_id=4, project_id=180, dataset_id=55, view_id=1039),
            input_file=input_file,
        )
    )

    assert fake_service.view_call_log == [
        (1039, "math", {"dataset_id": 55, "expression": "Price * Qty"})
    ]
