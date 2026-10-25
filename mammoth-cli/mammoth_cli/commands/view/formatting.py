"""Exportable-config and conditional-format handlers."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import (
    _DISPLAY_NAME_KEY,
    _INTERNAL_NAME_KEY,
    _forward_optional,
    _int_positional_at,
    _meta,
    _require_field,
    _require_int_positional_at,
    _resolve_dataset_id,
    _symbol,
)
from mammoth_cli.commands.view.columns import (
    _dataview_metadata,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_FIELD,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
    require_project,
)
from mammoth_cli.services import conditional_format as cf_rules


def view_exportable_config_get(invocation: Invocation) -> HandlerResult:
    """Get a dataview's exportable pipeline configuration."""
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    if view_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT, message="view id must be positive.", exit_status=EXIT_USAGE
        )
    document = invocation.load_input() or {}
    explicit_dataset = _int_positional_at(invocation, 1, "dataset id")
    if explicit_dataset is None and document.get("dataset_id") is not None:
        explicit_dataset = int(document["dataset_id"])
    if explicit_dataset is not None and explicit_dataset <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="dataset id must be positive.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=view_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_exportable_config_apply(invocation: Invocation) -> HandlerResult:
    """Apply exactly one exportable config or clipboard item list."""
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    if view_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT, message="view id must be positive.", exit_status=EXIT_USAGE
        )
    document = invocation.load_input() or {}
    explicit_dataset = _int_positional_at(invocation, 1, "dataset id")
    if explicit_dataset is None and document.get("dataset_id") is not None:
        explicit_dataset = int(document["dataset_id"])
    if explicit_dataset is not None and explicit_dataset <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="dataset id must be positive.",
            exit_status=EXIT_USAGE,
        )
    items = document.get("items")
    config = document.get("config")
    if (items is None) == (config is None):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Exactly one of 'items' or 'config' is required.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"apply exportable config to view {view_id}",
        target=str(view_id),
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "items": items,
            "config": config,
            "project_id": project_id,
        }
        _forward_optional(document, kwargs, ("insert_after_sequence", "is_paste_mode"))
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_create(invocation: Invocation) -> HandlerResult:
    """Colour cells in many columns by one threshold in a single command (columns + operator + value + color): each cell is judged by its own value. applies_to=row colours whole rows when any/all of the columns match.

    Per-cell means one rule per column, all made in this one call. A raw ``rule`` body still
    works instead.
    """  # noqa: E501
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    has_typed = _cf_check_document(document)
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        rules = _cf_rules_for_document(
            service, document, has_typed, (dataset_id, dataview_id, project_id)
        )
        data = _create_cf_rules(service, invocation, rules, (dataset_id, dataview_id, project_id))
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_replace(invocation: Invocation) -> HandlerResult:
    """Replace every conditional-format rule on a view with new ones in one call.

    Takes the input of ``view conditional-format create`` (typed fields or a raw ``rule``);
    the old rules are deleted and the new ones created. Prompt or ``--yes``.
    """
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    has_typed = _cf_check_document(document)
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        scope = (dataset_id, dataview_id, project_id)
        rules = _cf_rules_for_document(service, document, has_typed, scope)
        enforce_confirmation(
            invocation,
            policy=POLICY_PROMPT_OR_YES,
            action=f"replace all conditional-format rules on view {dataview_id}",
        )
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            rules=rules,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def _cf_check_document(document: dict[str, Any]) -> bool:
    """Whether the input uses the typed fields; refuses mixing them with ``rule`` or neither."""
    has_typed = any(field in document for field in cf_rules.TYPED_FIELDS)
    if "rule" in document and has_typed:
        raise CliError(
            code=cf_rules.CODE_INVALID_RULE,
            message="Pass either 'rule' or the typed fields (columns, operator, value, color).",
            exit_status=EXIT_USAGE,
        )
    if "rule" not in document and not has_typed:
        _require_field(document, "rule")
    return has_typed


def _cf_rules_for_document(
    service: Any, document: dict[str, Any], has_typed: bool, scope: tuple[Any, ...]
) -> list[dict[str, Any]]:
    """The rule bodies an input document stands for (typed fields build one rule per column)."""
    dataset_id, dataview_id, project_id = scope
    if has_typed:
        metadata = _dataview_metadata(service, dataset_id, dataview_id, project_id)
        column_map, column_types = _column_maps(metadata)
        return cf_rules.build_rules(document, column_map, column_types)
    cf_rules.validate_rule(document["rule"])
    return [document["rule"]]


def _cf_sequence(rule: Any) -> int:
    return rule.get("SEQUENCE", -1) if isinstance(rule, dict) else -1


def _create_cf_rules(
    service: Any, invocation: Invocation, rules: list[dict[str, Any]], scope: tuple[Any, ...]
) -> Any:
    """POST each rule in turn; a mid-way failure names the rule ids already created.

    Every response is the dataview's whole rule map; the new rule has the highest SEQUENCE.
    """
    dataset_id, dataview_id, project_id = scope
    ids: list[str] = []
    data: Any = None
    for rule in rules:
        try:
            data = service.call(
                _symbol(invocation),
                dataset_id=dataset_id,
                dataview_id=dataview_id,
                rule=rule,
                project_id=project_id,
            )
        except DryRunStop as stop:
            stop.record["rules"] = rules  # every body that would be sent, not just the first
            raise
        except CliError as error:
            if ids:
                error.details = {**error.details, "created_rule_ids": ids}
                error.message += f" Rules already created before the failure: {ids}."
            raise
        if isinstance(data, dict) and data:
            ids.append(max(data, key=lambda k: _cf_sequence(data[k])))
    if len(rules) == 1:
        return data
    note = f"{len(rules)} rules, one per column, so each cell is coloured by its own value."
    return {"created_rule_ids": ids, "rules_created": len(rules), "note": note}


def _column_maps(metadata: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
    """Display -> internal name and display -> type maps from a view's column metadata."""
    names: dict[str, str] = {}
    types: dict[str, str] = {}
    for column in metadata:
        internal = column.get(_INTERNAL_NAME_KEY)
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(internal, str) and isinstance(display, str):
            names[display] = internal
            if isinstance(column.get("type"), str):
                types[display] = column["type"]
    return names, types


def view_conditional_format_delete_all(invocation: Invocation) -> HandlerResult:
    """Delete a conditional-format rule on a dataview. Prompt or ``--yes``.

    The release route deletes one rule per call and requires ``rule_id`` as a
    query parameter (``view conditional-format list`` shows the ids).
    """
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    rule_id = document.get("rule_id")
    if rule_id is None:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="This command requires the 'rule_id' input field.",
            exit_status=EXIT_USAGE,
            hint="List rules with 'view conditional-format list VIEW_ID', then pass "
            "--input '{\"rule_id\": ...}'.",
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete conditional-format rule {rule_id} on view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            rule_id=rule_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_list(invocation: Invocation) -> HandlerResult:
    """List conditional-format rules on a dataview."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_update(invocation: Invocation) -> HandlerResult:
    """Update a conditional-format rule on a dataview. ``rule`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    rule = _require_field(document, "rule")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            rule=rule,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + checkpoint_id (project-scoped)
# ---------------------------------------------------------------------------
