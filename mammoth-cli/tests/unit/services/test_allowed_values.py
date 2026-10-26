"""Allowed values show in ``--help`` and in the error hint, from the validator's own list.

An input that takes one of a fixed list of words must say which words, both
before the call (``--help``) and when a wrong one is refused (the ``hint``).
The help line and the hint are generated from the same tuple the validator
checks against, so the three cannot drift apart.
"""

from __future__ import annotations

import pytest

from mammoth_cli.commands.dataset.create import _default_data_pull_file
from mammoth_cli.commands.view_ops.batch import _batch_steps
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.command_contract import resolve_command_contract
from mammoth_cli.services.field_enums import BATCH_OPS, DATA_PULL_FILE_VALUES, NESTED_CHOICES
from mammoth_cli.testing import make_runner


def _help(command_path: str) -> str:
    return " ".join(make_runner().invoke_help(command_path).split())


@pytest.mark.parametrize(
    ("command_id", "path"),
    [(command_id, path) for command_id, paths in NESTED_CHOICES.items() for path in paths],
)
def test_every_nested_choice_is_listed_in_the_commands_help(command_id: str, path: str) -> None:
    text = _help(command_id.replace(".", " "))
    assert path in text
    for value in NESTED_CHOICES[command_id][path]:
        assert value in text


def test_batch_accepts_exactly_the_listed_ops() -> None:
    for op in BATCH_OPS:
        _batch_steps({"steps": [{"op": op, "input": {}}]})
    with pytest.raises(CliError):
        _batch_steps({"steps": [{"op": "join", "input": {}}]})


def test_a_refused_batch_op_lists_every_allowed_op_in_the_hint() -> None:
    with pytest.raises(CliError) as caught:
        _batch_steps({"steps": [{"op": "join", "input": {}}]})
    error = caught.value
    assert error.hint is not None
    for op in BATCH_OPS:
        assert op in error.hint
    assert error.details["allowed"] == list(BATCH_OPS)
    assert error.details["got"] == "join"


def test_a_misspelt_batch_op_is_named() -> None:
    with pytest.raises(CliError) as caught:
        _batch_steps({"steps": [{"op": "fiter", "input": {}}]})
    assert caught.value.details["did_you_mean"] == "filter"


def test_data_pull_file_accepts_exactly_the_listed_values_and_hints_them() -> None:
    for value in DATA_PULL_FILE_VALUES:
        _default_data_pull_file(
            "cloud", {"query_properties": {"file_path": "a.csv", "data_pull_file": value}}
        )
    with pytest.raises(CliError) as caught:
        _default_data_pull_file(
            "cloud", {"query_properties": {"file_path": "a.csv", "data_pull_file": "latest"}}
        )
    for value in DATA_PULL_FILE_VALUES:
        assert value in (caught.value.hint or "")


@pytest.mark.parametrize(
    ("command_id", "field"),
    [("view.transform.extract-date", "component"), ("view.export.list", "handler_type")],
)
def test_help_lists_every_value_of_a_long_enum_not_the_first_six(
    command_id: str, field: str
) -> None:
    contract = resolve_command_contract(command_id)
    assert contract is not None
    values = next(f.enum_values for f in contract.accepted_fields if f.name == field)
    assert len(values) > 6
    text = _help(command_id.replace(".", " "))
    for value in values:
        assert str(value) in text
