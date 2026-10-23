"""A date or math step on a column of the wrong type is refused before any task is added."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view_ops
from mammoth_cli.commands.view_ops import transforms as view_transforms
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation, ResourceRef
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_GET = view_ops._DATAVIEW_GET_SYMBOL


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


_VIEW = {
    "id": 3,
    "metadata": [
        {"display_name": "Order Date", "internal_name": "column_a", "type": "DATE"},
        {"display_name": "Ship Date", "internal_name": "column_b", "type": "TEXT"},
        {"display_name": "Qty", "internal_name": "column_c", "type": "NUMERIC"},
        {"display_name": "Price", "internal_name": "column_d", "type": "TEXT"},
    ],
}


def _run(
    handler: Any, command_id: str, payload: dict[str, Any], tmp_path: Path
) -> FakeMammothService | None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    handler(
        Invocation(
            command_id=command_id,
            extra_args=["3"],
            resource_ref=ResourceRef(dataset_id=122, view_id=3),
            input_file=str(doc),
        )
    )
    return None


@pytest.fixture
def service(fake_service: FakeMammothService) -> FakeMammothService:
    fake_service.responses[_GET] = _VIEW
    return fake_service


@pytest.mark.parametrize(
    ("handler", "command_id", "payload", "column", "actual"),
    [
        (
            view_transforms.view_transform_extract_date,
            "view.transform.extract-date",
            {"column": "Ship Date", "component": "year"},
            "Ship Date",
            "TEXT",
        ),
        (
            view_transforms.view_transform_extract_date,
            "view.transform.extract-date",
            {"column": "Qty", "component": "year"},
            "Qty",
            "NUMERIC",
        ),
        (
            view_transforms.view_transform_increment_date,
            "view.transform.increment-date",
            {"column": "Ship Date", "delta": {"days": 1}},
            "Ship Date",
            "TEXT",
        ),
        (
            view_transforms.view_transform_date_diff,
            "view.transform.date-diff",
            {"component": "DAY", "start": "Order Date", "end": "Ship Date"},
            "Ship Date",
            "TEXT",
        ),
        (
            view_transforms.view_transform_math,
            "view.transform.math",
            {"expression": "Qty * Price", "new_column": "Total"},
            "Price",
            "TEXT",
        ),
    ],
    ids=["extract-text", "extract-numeric", "increment", "date-diff", "math"],
)
def test_a_wrong_typed_column_is_refused_before_the_write(
    service: FakeMammothService,
    tmp_path: Path,
    handler: Any,
    command_id: str,
    payload: dict[str, Any],
    column: str,
    actual: str,
) -> None:
    with pytest.raises(CliError) as caught:
        _run(handler, command_id, payload, tmp_path)
    error = caught.value
    assert error.code == "column_type_mismatch"
    assert error.details["column"] == column and error.details["actual_type"] == actual
    assert service.view_call_log == []


def test_a_text_column_gets_the_convert_type_command(
    service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as caught:
        _run(
            view_transforms.view_transform_extract_date,
            "view.transform.extract-date",
            {"column": "Ship Date", "component": "year"},
            tmp_path,
        )
    command = caught.value.recovery_commands[0]
    assert command.startswith("mammoth view transform convert-type 3 --input ")
    assert json.loads(command.split("--input ", 1)[1].strip("'")) == {
        "conversions": [{"column": "Ship Date", "to": "DATE"}]
    }


def test_matching_types_go_through(service: FakeMammothService, tmp_path: Path) -> None:
    _run(
        view_transforms.view_transform_extract_date,
        "view.transform.extract-date",
        {"column": "Order Date", "component": "year"},
        tmp_path,
    )
    _run(
        view_transforms.view_transform_math,
        "view.transform.math",
        {"expression": "Qty * 2", "new_column": "Double"},
        tmp_path,
    )
    assert [call[1] for call in service.view_call_log] == ["extract_date", "math"]


def test_an_unreadable_view_does_not_block_the_write(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_GET] = CliError(code="api_error", message="no")
    _run(
        view_transforms.view_transform_extract_date,
        "view.transform.extract-date",
        {"column": "Ship Date", "component": "year"},
        tmp_path,
    )
    assert [call[1] for call in fake_service.view_call_log] == ["extract_date"]
