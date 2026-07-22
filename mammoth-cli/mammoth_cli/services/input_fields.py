"""Command input fields that the CLI, rather than the SDK call, supplies."""

from __future__ import annotations

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
}


def excluded_input_fields(command_id: str) -> frozenset[str]:
    """Return SDK parameters that are not accepted from ``--input``."""
    context_fields = {"project_id", "workspace_id"}
    positional_fields = {
        item.name for item in resolve_positionals(command_id) if item.falls_back_to_field is None
    }
    return frozenset(context_fields | positional_fields) | _HANDLER_OWNED_FIELDS.get(
        command_id, frozenset()
    )


def handler_owned_fields(command_id: str) -> frozenset[str]:
    """Return only fields consumed, replaced, or intentionally omitted by a handler."""
    return _HANDLER_OWNED_FIELDS.get(command_id, frozenset())
