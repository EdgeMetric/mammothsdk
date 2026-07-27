"""Command input fields that the CLI, rather than the SDK call, supplies."""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.positionals import resolve_positionals

_HANDLER_OWNED_FIELDS: dict[str, frozenset[str]] = {
    # Skill handlers deliberately derive filesystem roots from the running
    # process and generate their own backup timestamp.  User input must not
    # claim to control values that the handlers replace or omit.
    "skill.install": frozenset({"home", "cwd", "timestamp"}),
    "skill.update": frozenset({"home", "cwd", "timestamp"}),
    "skill.uninstall": frozenset({"home", "cwd"}),
    "skill.path": frozenset({"home", "cwd"}),
    # ``job get`` is an immediate status read; only wait commands implement
    # the CLI's timeout/polling behavior.
    "job.get": frozenset({"timeout"}),
    # ``PipelineAPI.get_draft_status`` carries a legacy ``dataset_id`` alongside
    # the ``dataview_id`` the handler forwards from the view positional; the
    # handler never reads it, so it must not be advertised as an --input field.
    "view.draft.status": frozenset({"dataset_id"}),
}


#: Extra ``--input`` fields to weave into a command's generated ``agent_example``.
#: A few commands enforce a runtime "exactly one of" / identifier requirement that
#: the SDK signature marks optional (so the auto-generated example, which only fills
#: signature-required fields, omits it and is not actually runnable as shown). Each
#: value here is a genuine, accepted --input field so the documented example both
#: validates against the input schema and works when run.
_EXAMPLE_INPUT_HINTS: dict[str, dict[str, Any]] = {
    # AddonsAPI.add_connector/remove_connector require exactly one of
    # ``connector_id``/``connector_ids``; both are optional in the signature.
    "addon.connector.add": {"connector_id": 42},
    "addon.connector.remove": {"connector_id": 42},
    # The generic SDK types cannot express the creation-type-specific dataset
    # shape. Use the public sample CSV so help and generated references show a
    # request a new customer can understand and run.
    "dataset.create": {
        "ds_creation_type": "weburl",
        "dataset_spec": {
            "url": "https://sampledata.mammoth.io/Multi-Store_Retail_Sales.csv"
        },
    },
    # project user update targets a specific member: the handler requires ``role``
    # (auto-filled) plus one of ``user_id``/``invite_id`` to say *which* member.
    "project.user.update": {"user_id": 123},
}


def example_input_hints(command_id: str) -> dict[str, Any]:
    """Return extra ``--input`` fields to include in the generated example."""
    return dict(_EXAMPLE_INPUT_HINTS.get(command_id, {}))


def excluded_input_fields(command_id: str) -> frozenset[str]:
    """Return SDK parameters that are not accepted from ``--input``."""
    context_fields = {"project_id", "workspace_id"}
    positional_fields: set[str] = set()
    for item in resolve_positionals(command_id):
        if item.falls_back_to_field is not None:
            # Dual-sourced: the field is still a legitimate --input key.
            continue
        positional_fields.add(item.name)
        if item.fills_sdk_param is not None:
            # The positional also supplies this (differently named) SDK argument.
            positional_fields.add(item.fills_sdk_param)
    return frozenset(context_fields | positional_fields) | _HANDLER_OWNED_FIELDS.get(
        command_id, frozenset()
    )


def handler_owned_fields(command_id: str) -> frozenset[str]:
    """Return only fields consumed, replaced, or intentionally omitted by a handler."""
    return _HANDLER_OWNED_FIELDS.get(command_id, frozenset())
