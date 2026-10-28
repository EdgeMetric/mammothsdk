"""Every create-type command result carries its resource id at the top level (D3).

The API names a new resource's id differently per endpoint, and a finished job nests it as
``response.dataset_id``. ``with_resource_ids`` gives every result one documented key,
``<resource>_id``, so a script never has to know which shape a command replied with.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import mammoth_cli
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.resource_ids import (
    CREATE_RESOURCES,
    id_key,
    is_create_command,
    resource_name,
    with_resource_ids,
)

_CREATE_COMMANDS = sorted(
    record["command_id"] for record in load_commands() if is_create_command(record["command_id"])
)
_MAKING = sorted(command for command, created in CREATE_RESOURCES.items() if created)
_SKIPPED = sorted(command for command, created in CREATE_RESOURCES.items() if created is None)
#: Reply shapes the API uses for a made resource, as functions of the documented key.
_SHAPES: dict[str, Any] = {
    "own key": lambda key: {key: 7, "name": "x"},
    "nested in response": lambda key: {"status": "done", "response": {key: 7}},
}


def test_every_create_command_is_classified_and_every_entry_is_a_command() -> None:
    """A new create command must say which resource it makes, or that its reply has no id."""
    assert set(CREATE_RESOURCES) == set(_CREATE_COMMANDS)


@pytest.mark.parametrize("command_id", _CREATE_COMMANDS)
def test_an_entry_names_the_resource_the_command_makes(command_id: str) -> None:
    """The noun in the command id is not always the resource: spot the odd ones explicitly."""
    expected = {
        "view.variants.create": None,
        "billing.stripe.create": "subscription",
        "agent.access.request.create": "access_request",
        "parameter.group.create": "parameter_group",
        "view.data-check.create": "data_check",
        "batch.create-spec": "batch",
        "project.copy": None,
    }
    if command_id in expected:
        assert resource_name(command_id) == expected[command_id]
    elif CREATE_RESOURCES[command_id]:
        resource = resource_name(command_id)
        assert resource is not None and not resource.endswith("s"), (command_id, resource)


@pytest.mark.parametrize("command_id", _MAKING)
@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_a_create_result_exposes_its_resource_id_at_the_top_level(
    command_id: str, shape: str
) -> None:
    resource = resource_name(command_id)
    assert resource is not None
    key = id_key(resource)

    result = with_resource_ids(command_id, _SHAPES[shape](key), {})

    assert result[key] == 7


@pytest.mark.parametrize("command_id", _MAKING)
def test_the_bare_id_is_read_only_where_the_entry_says_it_is_the_resources(
    command_id: str,
) -> None:
    created = CREATE_RESOURCES[command_id]
    assert created is not None

    result = with_resource_ids(command_id, {"id": 7, "name": "x"}, {})

    assert (result.get(id_key(created.resource)) == 7) is created.plain_id


@pytest.mark.parametrize("command_id", _SKIPPED)
def test_a_skipped_command_gets_no_derived_key(command_id: str) -> None:
    reply = {"id": 7, "job_id": 3, "view_ids": [1, 2]}

    assert with_resource_ids(command_id, reply, {}) is reply


@pytest.mark.parametrize("old_key", ["identity_key", "connection_key"])
def test_connection_create_adds_connection_id_and_keeps_the_old_key(old_key: str) -> None:
    reply = {old_key: "conn_abc", "connection_config": {}}

    result = with_resource_ids("connector.connection.create", reply, {})

    assert result["connection_id"] == "conn_abc"
    assert result[old_key] == "conn_abc"


def test_a_job_result_lifts_the_dataset_id_it_produced() -> None:
    reply = {"job_id": 9, "status": "completed", "response": {"dataset_id": 42}}

    result = with_resource_ids("job.wait", reply, {})

    assert result["dataset_id"] == 42
    assert result["response"] == {"dataset_id": 42}
    assert "id" not in result


def test_a_write_that_made_a_dataset_reports_it_through_meta_opens() -> None:
    meta = {"opens": [{"kind": "dataset", "id": 5, "url": "u", "created": True}]}

    result = with_resource_ids("file.upload", {"job_id": 1, "result": {"dataset_id": 5}}, meta)

    assert result["dataset_id"] == 5


def test_an_existing_top_level_id_is_never_replaced() -> None:
    result = with_resource_ids(
        "dataset.create", {"dataset_id": 1, "response": {"dataset_id": 2}}, {}
    )

    assert result["dataset_id"] == 1


def test_no_id_is_invented_when_the_reply_has_none() -> None:
    reply = {"status": "pending", "job_id": 3}

    assert with_resource_ids("dataset.create", reply, {}) is reply


def test_a_read_or_edit_result_is_left_alone() -> None:
    reply = {"id": 7, "name": "x"}

    assert with_resource_ids("dataset.get", reply, {}) is reply
    assert with_resource_ids("dataset.update", reply, {}) is reply


def test_the_skill_reference_documents_the_rule() -> None:
    skill = Path(mammoth_cli.__file__).parent / "bundled_skill" / "mammoth-cli"
    text = (skill / "references" / "machine-output.md").read_text("utf-8")

    assert "## Resource ids in results" in text
    assert "`connection_id`" in text
