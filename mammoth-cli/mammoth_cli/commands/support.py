"""Handlers for the ``support`` command family (workspace/admin operations).

Unlike most command families, ``support`` operations are not scoped to the
active project or even the SDK client's own workspace: every command targets
an explicit resource passed by the caller (a workspace id, plan id, connector
id, profile id, or user email), and every command is reviewed as
``high_impact`` with a ``confirm_target`` confirmation policy. Handlers
dispatch through the generic :meth:`~mammoth_cli.services.protocol.MammothService.call`
seam to the public SDK method named by the command's reviewed manifest
``sdk_symbol``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.local_files import refuse_existing_file

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _bound_document(invocation: Invocation) -> dict[str, Any]:
    """Return admitted input after the shared S7 contract binding boundary."""
    return bind_command_inputs(invocation.command_id, invocation.load_input() or {})


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent."""
    return invocation.extra_args[0] if invocation.extra_args else None


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent."""
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument parsed as an int, or raise usage."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_positional_or_field(
    invocation: Invocation, document: dict[str, Any] | None, field: str, human: str
) -> str:
    """Return a required string from the first positional or an input field."""
    value = _string_positional(invocation) or (document.get(field) if document else None)
    if not value:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"A {human} is required.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {human} as a positional argument or a '{field}' input field.",
        )
    return str(value)


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy every admitted input field into ``kwargs`` unchanged."""
    for field, value in document.items():
        if field in kwargs and field not in fields:
            continue
        kwargs[field] = value


CONNECTOR_PRICE_REMOVED = (
    "`price_per_month` has no effect on connectors: the server no longer has a price "
    "on them (they are access, not a priced line item), and the SDK does not send it. "
    "Remove it from the input."
)


def _connector_price_notes(document: dict[str, Any]) -> list[str]:
    """Say so when the input still carries the removed connector ``price_per_month``."""
    return [CONNECTOR_PRICE_REMOVED] if "price_per_month" in document else []


def _with_warnings(data: Any, warnings: list[str]) -> Any:
    """Attach ``warnings`` to a dict result; leave anything else as the server sent it."""
    if warnings and isinstance(data, dict):
        return {**data, "warnings": warnings}
    return data


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a support command (no project scope)."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": None,
    }


def _confirm(invocation: Invocation, *, action: str, target: str) -> None:
    """Enforce the ``confirm_target`` policy every support command carries."""
    enforce_confirmation(invocation, policy=POLICY_CONFIRM_TARGET, action=action, target=target)


# -- Connectors ---------------------------------------------------------------


def support_connector_list(invocation: Invocation) -> HandlerResult:
    """List all subscription connectors."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_connector_create(invocation: Invocation) -> HandlerResult:
    """Create a connector. Name comes from a positional or the ``name`` field."""
    document = _bound_document(invocation)
    name = _require_positional_or_field(invocation, document, "name", "connector name")
    kwargs: dict[str, Any] = {"name": name}
    notes = _connector_price_notes(document)
    _forward_optional(document, kwargs, ("description", "price_per_month", "enabled"))
    _confirm(invocation, action=f"create connector '{name}'", target=name)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return _with_warnings(data, notes), _meta(invocation, auth.workspace_id)


def support_connector_update(invocation: Invocation) -> HandlerResult:
    """Update a connector. Connector id is positional; fields come from ``--input``."""
    connector_id = _require_int_positional(invocation, "connector id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"connector_id": connector_id}
    notes = _connector_price_notes(document)
    _forward_optional(document, kwargs, ("name", "description", "price_per_month", "enabled"))
    _confirm(invocation, action=f"update connector {connector_id}", target=str(connector_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return _with_warnings(data, notes), _meta(invocation, auth.workspace_id)


def support_connector_delete(invocation: Invocation) -> HandlerResult:
    """Delete one connector by id."""
    connector_id = _require_int_positional(invocation, "connector id")
    _confirm(invocation, action=f"delete connector {connector_id}", target=str(connector_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), connector_id=connector_id)
    return data, _meta(invocation, auth.workspace_id)


# -- Connector profiles ---------------------------------------------------------


def support_connector_profile_list(invocation: Invocation) -> HandlerResult:
    """List all connector profiles."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_connector_profile_create(invocation: Invocation) -> HandlerResult:
    """Create a connector profile. Name comes from a positional or ``name`` field."""
    document = _bound_document(invocation)
    name = _require_positional_or_field(invocation, document, "name", "connector profile name")
    kwargs: dict[str, Any] = {"name": name}
    _forward_optional(document, kwargs, ("description", "connectors"))
    _confirm(invocation, action=f"create connector profile '{name}'", target=name)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_connector_profile_update(invocation: Invocation) -> HandlerResult:
    """Update a connector profile. Profile id is positional; fields from ``--input``."""
    profile_id = _require_int_positional(invocation, "profile id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"profile_id": profile_id}
    _forward_optional(document, kwargs, ("name", "description", "connectors"))
    _confirm(invocation, action=f"update connector profile {profile_id}", target=str(profile_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_connector_profile_delete(invocation: Invocation) -> HandlerResult:
    """Delete one connector profile by id."""
    profile_id = _require_int_positional(invocation, "profile id")
    _confirm(invocation, action=f"delete connector profile {profile_id}", target=str(profile_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), profile_id=profile_id)
    return data, _meta(invocation, auth.workspace_id)


def support_connector_profile_add_connector(invocation: Invocation) -> HandlerResult:
    """Add a connector to a connector profile. Profile id is positional."""
    profile_id = _require_int_positional(invocation, "profile id")
    document = _bound_document(invocation)
    connector_id = invocation.positional("connector_id")
    if connector_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A connector id is required.",
            exit_status=EXIT_USAGE,
        )
    connector_id = int(connector_id)
    kwargs: dict[str, Any] = {"profile_id": profile_id, "connector_id": connector_id}
    _forward_optional(document, kwargs, ("price_per_month", "enabled"))
    _confirm(
        invocation,
        action=f"add connector to connector profile {profile_id}",
        target=str(profile_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


# -- Features -------------------------------------------------------------------


def support_feature_list(invocation: Invocation) -> HandlerResult:
    """List all subscription features."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_feature_create(invocation: Invocation) -> HandlerResult:
    """Create a feature. Name comes from a positional or the ``name`` field."""
    document = _bound_document(invocation)
    name = _require_positional_or_field(invocation, document, "name", "feature name")
    kwargs: dict[str, Any] = {"name": name}
    _forward_optional(document, kwargs, ("description", "price_per_month", "enabled", "values"))
    _confirm(invocation, action=f"create feature '{name}'", target=name)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_feature_update(invocation: Invocation) -> HandlerResult:
    """Update a feature. Feature id is positional; fields come from ``--input``."""
    feature_id = _require_int_positional(invocation, "feature id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"feature_id": feature_id}
    _forward_optional(
        document, kwargs, ("name", "description", "price_per_month", "enabled", "values")
    )
    _confirm(invocation, action=f"update feature {feature_id}", target=str(feature_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_feature_delete(invocation: Invocation) -> HandlerResult:
    """Delete one feature by id."""
    feature_id = _require_int_positional(invocation, "feature id")
    _confirm(invocation, action=f"delete feature {feature_id}", target=str(feature_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), feature_id=feature_id)
    return data, _meta(invocation, auth.workspace_id)


# -- Feature profiles -------------------------------------------------------------


def support_feature_profile_list(invocation: Invocation) -> HandlerResult:
    """List all feature profiles."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_feature_profile_create(invocation: Invocation) -> HandlerResult:
    """Create a feature profile. Name comes from a positional or ``name`` field."""
    document = _bound_document(invocation)
    name = _require_positional_or_field(invocation, document, "name", "feature profile name")
    kwargs: dict[str, Any] = {"name": name}
    _forward_optional(document, kwargs, ("description", "features"))
    _confirm(invocation, action=f"create feature profile '{name}'", target=name)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_feature_profile_update(invocation: Invocation) -> HandlerResult:
    """Update a feature profile. Profile id is positional; fields from ``--input``."""
    profile_id = _require_int_positional(invocation, "profile id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"profile_id": profile_id}
    _forward_optional(document, kwargs, ("name", "description", "features"))
    _confirm(invocation, action=f"update feature profile {profile_id}", target=str(profile_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_feature_profile_delete(invocation: Invocation) -> HandlerResult:
    """Delete one feature profile by id."""
    profile_id = _require_int_positional(invocation, "profile id")
    _confirm(invocation, action=f"delete feature profile {profile_id}", target=str(profile_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), profile_id=profile_id)
    return data, _meta(invocation, auth.workspace_id)


def support_feature_profile_add_feature(invocation: Invocation) -> HandlerResult:
    """Add a feature to a feature profile. Profile id is positional."""
    profile_id = _require_int_positional(invocation, "profile id")
    document = _bound_document(invocation)
    feature_id = invocation.positional("feature_id")
    if feature_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT, message="A feature id is required.", exit_status=EXIT_USAGE
        )
    feature_id = int(feature_id)
    kwargs: dict[str, Any] = {"profile_id": profile_id, "feature_id": feature_id}
    _forward_optional(document, kwargs, ("price_per_month", "enabled", "value"))
    _confirm(
        invocation,
        action=f"add feature to feature profile {profile_id}",
        target=str(profile_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


# -- Ownership transfer -----------------------------------------------------------


def support_ownership_transfer(invocation: Invocation) -> HandlerResult:
    """Transfer ownership of a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    user_id = invocation.positional("user_id")
    if user_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT, message="A user id is required.", exit_status=EXIT_USAGE
        )
    user_id = int(user_id)
    kwargs: dict[str, Any] = {"workspace_id": workspace_id, "user_id": user_id}
    _forward_optional(document, kwargs, ("new_role", "remove_role"))
    _confirm(
        invocation,
        action=f"transfer ownership of workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


# -- Plans ------------------------------------------------------------------------

_PLAN_OPTIONAL = (
    "display_name",
    "description",
    "annual_price",
    "annual_only",
    "trial_days",
    "storage_amount",
    "max_storage",
    "max_users",
    "no_of_users",
    "seat_price",
    "number_of_tiers",
    "storage_block_size",
    "tiers",
    "connector_profile_id",
    "feature_profile_id",
)

_PLAN_UPDATE_OPTIONAL = ("name", "monthly_price", "is_self_serve") + _PLAN_OPTIONAL


def support_plan_list(invocation: Invocation) -> HandlerResult:
    """List all subscription plans."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_plan_self_serve_list(invocation: Invocation) -> HandlerResult:
    """List self-serve subscription plans."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_plan_chargebee_list(invocation: Invocation) -> HandlerResult:
    """List available Chargebee plans/resources."""
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("resource",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_get(invocation: Invocation) -> HandlerResult:
    """Get one subscription plan by id."""
    plan_id = _require_int_positional(invocation, "plan id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_create(invocation: Invocation) -> HandlerResult:
    """Create a subscription plan. Name is positional; required fields from ``--input``."""
    document = _bound_document(invocation)
    name = _require_positional_or_field(invocation, document, "name", "plan name")
    monthly_price = _require_field(document, "monthly_price")
    is_self_serve = _require_field(document, "is_self_serve")
    kwargs: dict[str, Any] = {
        "name": name,
        "monthly_price": monthly_price,
        "is_self_serve": is_self_serve,
    }
    _forward_optional(document, kwargs, _PLAN_OPTIONAL)
    _confirm(invocation, action=f"create plan '{name}'", target=name)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_update(invocation: Invocation) -> HandlerResult:
    """Update a subscription plan. Plan id is positional; fields from ``--input``."""
    plan_id = _require_int_positional(invocation, "plan id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"plan_id": plan_id}
    _forward_optional(document, kwargs, _PLAN_UPDATE_OPTIONAL)
    _confirm(invocation, action=f"update plan {plan_id}", target=str(plan_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_delete(invocation: Invocation) -> HandlerResult:
    """Delete one subscription plan by id."""
    plan_id = _require_int_positional(invocation, "plan id")
    _confirm(invocation, action=f"delete plan {plan_id}", target=str(plan_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_update_storage_tiers(invocation: Invocation) -> HandlerResult:
    """Replace a plan's storage pricing tiers. Plan id is positional."""
    plan_id = _require_int_positional(invocation, "plan id")
    document = _bound_document(invocation)
    storage_tiers = _require_field(document, "storage_tiers")
    _confirm(invocation, action=f"update storage tiers for plan {plan_id}", target=str(plan_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id, storage_tiers=storage_tiers)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_archive(invocation: Invocation) -> HandlerResult:
    """Archive one subscription plan by id."""
    plan_id = _require_int_positional(invocation, "plan id")
    _confirm(invocation, action=f"archive plan {plan_id}", target=str(plan_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id)
    return data, _meta(invocation, auth.workspace_id)


def _require_named_int(invocation: Invocation, name: str, human: str) -> int:
    """Return a required integer positional by its declared name, or raise usage."""
    raw = invocation.positional(name)
    if raw is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT, message=f"A {human} is required.", exit_status=EXIT_USAGE
        )
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {human} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def support_plan_unarchive(invocation: Invocation) -> HandlerResult:
    """Platform admin only: unarchive one subscription plan by id."""
    plan_id = _require_int_positional(invocation, "plan id")
    _confirm(invocation, action=f"unarchive plan {plan_id}", target=str(plan_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_storage_option_list(invocation: Invocation) -> HandlerResult:
    """Platform admin only: list a plan's storage options, archived ones included."""
    plan_id = _require_int_positional(invocation, "plan id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_storage_option_create(invocation: Invocation) -> HandlerResult:
    """Platform admin only: add a storage option (total GB and prices) to a plan."""
    plan_id = _require_int_positional(invocation, "plan id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {
        "plan_id": plan_id,
        "storage_gb": _require_field(document, "storage_gb"),
        "monthly_price": _require_field(document, "monthly_price"),
        "annual_price": _require_field(document, "annual_price"),
    }
    _confirm(invocation, action=f"add a storage option to plan {plan_id}", target=str(plan_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_storage_option_update(invocation: Invocation) -> HandlerResult:
    """Platform admin only: re-price or resize one storage option of a plan."""
    plan_id = _require_int_positional(invocation, "plan id")
    option_id = _require_named_int(invocation, "option_id", "storage option id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"plan_id": plan_id, "option_id": option_id}
    _forward_optional(document, kwargs, ("storage_gb", "monthly_price", "annual_price"))
    _confirm(
        invocation,
        action=f"update storage option {option_id} of plan {plan_id}",
        target=str(option_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_storage_option_archive(invocation: Invocation) -> HandlerResult:
    """Platform admin only: archive one storage option of a plan (never deleted)."""
    plan_id = _require_int_positional(invocation, "plan id")
    option_id = _require_named_int(invocation, "option_id", "storage option id")
    _confirm(
        invocation,
        action=f"archive storage option {option_id} of plan {plan_id}",
        target=str(option_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id, option_id=option_id)
    return data, _meta(invocation, auth.workspace_id)


# -- Subscriptions ------------------------------------------------------------------


def support_subscription_get(invocation: Invocation) -> HandlerResult:
    """Get a workspace's Chargebee subscription details. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"workspace_id": workspace_id}
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_subscription_create(invocation: Invocation) -> HandlerResult:
    """Register a workspace's Chargebee subscription. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    plan_id = invocation.positional("plan_id")
    if plan_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT, message="A plan id is required.", exit_status=EXIT_USAGE
        )
    plan_id = str(plan_id)
    kwargs: dict[str, Any] = {"workspace_id": workspace_id, "plan_id": plan_id}
    _forward_optional(
        document, kwargs, ("customer_id", "first_name", "last_name", "email", "company_name")
    )
    _confirm(
        invocation,
        action=f"create subscription for workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_subscription_update(invocation: Invocation) -> HandlerResult:
    """Update a workspace's Chargebee subscription id. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    _bound_document(invocation)
    subscription_id = invocation.positional("subscription_id")
    if subscription_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A subscription id is required.",
            exit_status=EXIT_USAGE,
        )
    subscription_id = str(subscription_id)
    _confirm(
        invocation,
        action=f"update subscription for workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), workspace_id=workspace_id, subscription_id=subscription_id
        )
    return data, _meta(invocation, auth.workspace_id)


# -- Users (global) -------------------------------------------------------------------


def support_user_list_all(invocation: Invocation) -> HandlerResult:
    """List users across workspaces."""
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("fields", "sort", "offset", "limit"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_user_register(invocation: Invocation) -> HandlerResult:
    """Register a new user. Email is positional; required fields from ``--input``."""
    document = _bound_document(invocation)
    email = _require_positional_or_field(invocation, document, "email", "user email")
    first_name = _require_field(document, "first_name")
    last_name = _require_field(document, "last_name")
    verified = _require_field(document, "verified")
    kwargs: dict[str, Any] = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "verified": verified,
    }
    _forward_optional(document, kwargs, ("is_registration",))
    _confirm(invocation, action=f"register user '{email}'", target=email)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_user_update(invocation: Invocation) -> HandlerResult:
    """Update a user's verification status. Email is positional."""
    document = _bound_document(invocation)
    email = _require_positional_or_field(invocation, document, "email", "user email")
    verified = _require_field(document, "verified")
    kwargs: dict[str, Any] = {"email": email, "verified": verified}
    _forward_optional(document, kwargs, ("is_registration",))
    _confirm(invocation, action=f"update user '{email}'", target=email)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


# -- Workspaces (support/admin) -------------------------------------------------------


def support_workspace_list(invocation: Invocation) -> HandlerResult:
    """List all workspaces visible to the current admin/support user."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_get(invocation: Invocation) -> HandlerResult:
    """Get details of a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"workspace_id": workspace_id}
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_create(invocation: Invocation) -> HandlerResult:
    """Create a workspace. Name is positional; required fields from ``--input``."""
    document = _bound_document(invocation)
    name = _require_positional_or_field(invocation, document, "name", "workspace name")
    user_email = _require_field(document, "user_email")
    payment_frequency = _require_field(document, "payment_frequency")
    kwargs: dict[str, Any] = {
        "name": name,
        "user_email": user_email,
        "payment_frequency": payment_frequency,
    }
    _forward_optional(
        document,
        kwargs,
        (
            "plan_id",
            "origin",
            "is_verified",
            "is_registration",
            "file_id",
            "table_number",
            "plan_create",
        ),
    )
    _confirm(invocation, action=f"create workspace '{name}'", target=name)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_update(invocation: Invocation) -> HandlerResult:
    """Update a workspace's details/subscription. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    name = _require_field(document, "name")
    payment_frequency = _require_field(document, "payment_frequency")
    plan_id = _require_field(document, "plan_id")
    kwargs: dict[str, Any] = {
        "workspace_id": workspace_id,
        "name": name,
        "payment_frequency": payment_frequency,
        "plan_id": plan_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("plan_create", "plan_update"))
    _confirm(invocation, action=f"update workspace {workspace_id}", target=str(workspace_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_delete(invocation: Invocation) -> HandlerResult:
    """Delete one workspace by id."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    _confirm(invocation, action=f"delete workspace {workspace_id}", target=str(workspace_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), workspace_id=workspace_id)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_suspend_access(invocation: Invocation) -> HandlerResult:
    """Suspend user access to a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"workspace_id": workspace_id}
    _forward_optional(document, kwargs, ("reason",))
    _confirm(
        invocation,
        action=f"suspend access to workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_restore_access(invocation: Invocation) -> HandlerResult:
    """Restore user access to a suspended workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    _confirm(
        invocation,
        action=f"restore access to workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), workspace_id=workspace_id)
    return data, _meta(invocation, auth.workspace_id)


# -- Workspace users (support/admin) ---------------------------------------------------


def support_workspace_user_list(invocation: Invocation) -> HandlerResult:
    """List users in a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"workspace_id": workspace_id}
    _forward_optional(document, kwargs, ("limit", "offset", "fields", "sort"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_user_add(invocation: Invocation) -> HandlerResult:
    """Add a user to a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    email = _require_field(document, "email")
    role = _require_field(document, "role")
    kwargs: dict[str, Any] = {"workspace_id": workspace_id, "email": email, "role": role}
    assert document is not None
    _forward_optional(document, kwargs, ("first_name", "last_name"))
    _confirm(
        invocation,
        action=f"add user to workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_user_remove(invocation: Invocation) -> HandlerResult:
    """Remove a user from a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    _bound_document(invocation)
    user_id = invocation.positional("user_id")
    if user_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT, message="A user id is required.", exit_status=EXIT_USAGE
        )
    user_id = int(user_id)
    _confirm(
        invocation,
        action=f"remove user from workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), workspace_id=workspace_id, user_id=user_id)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_user_transfer(invocation: Invocation) -> HandlerResult:
    """Transfer/change a user's role within a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = _bound_document(invocation)
    user_id = invocation.positional("user_id")
    if user_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT, message="A user id is required.", exit_status=EXIT_USAGE
        )
    user_id = int(user_id)
    role = _require_field(document, "role")
    kwargs: dict[str, Any] = {"workspace_id": workspace_id, "user_id": user_id, "role": role}
    assert document is not None
    _forward_optional(document, kwargs, ("remove_role",))
    _confirm(
        invocation,
        action=f"transfer user role in workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


# -- Curated template catalog (dashboards v3 admin) ---------------------------------
#
# Every route refuses a caller without a Mammoth staff (platform-admin) role, and
# acts on CURATED templates only. The help line of each command says so first.


def _require_text_positional(invocation: Invocation, name: str, human: str) -> str:
    """Return a required string positional by its declared name, or raise usage."""
    value = invocation.positional(name)
    if not value:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"A {human} is required.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {human} as a positional argument.",
        )
    return str(value)


def _template_read(invocation: Invocation) -> HandlerResult:
    """Call a slug-addressed read of the curated catalog."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), slug=slug)
    return data, _meta(invocation, auth.workspace_id)


def _template_write(invocation: Invocation, verb: str) -> HandlerResult:
    """Call a slug-addressed write of the curated catalog after ``--confirm SLUG``."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    _confirm(invocation, action=f"{verb} curated template '{slug}'", target=slug)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), slug=slug)
    return data, _meta(invocation, auth.workspace_id)


def support_template_list(invocation: Invocation) -> HandlerResult:
    """Platform admin only: list every curated template, drafts and faults first."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_template_edit(invocation: Invocation) -> HandlerResult:
    """Platform admin only: edit a curated template's filing ('changes' from '--input')."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    document = _bound_document(invocation)
    changes = _require_field(document, "changes")
    _confirm(invocation, action=f"edit curated template '{slug}'", target=slug)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), slug=slug, changes=changes)
    return data, _meta(invocation, auth.workspace_id)


def support_template_data_preview(invocation: Invocation) -> HandlerResult:
    """Platform admin only: read up to 50 rows of the data a curated template opens on."""
    return _template_read(invocation)


def support_template_canvas(invocation: Invocation) -> HandlerResult:
    """Platform admin only: read a curated template's canvas, drafts included."""
    return _template_read(invocation)


def support_template_publish(invocation: Invocation) -> HandlerResult:
    """Platform admin only: take a curated draft live in every customer's gallery."""
    return _template_write(invocation, "publish")


def support_template_unpublish(invocation: Invocation) -> HandlerResult:
    """Platform admin only: take a live or retired curated template back to draft."""
    return _template_write(invocation, "unpublish")


def support_template_retire(invocation: Invocation) -> HandlerResult:
    """Platform admin only: retire a curated template (kept, no longer offered)."""
    return _template_write(invocation, "retire")


def support_template_thumbnail_clear(invocation: Invocation) -> HandlerResult:
    """Platform admin only: remove a curated template's picture."""
    return _template_write(invocation, "remove the picture of")


def support_template_discard(invocation: Invocation) -> HandlerResult:
    """Platform admin only: permanently remove a curated draft, its board and its data."""
    return _template_write(invocation, "discard")


def support_template_thumbnail_set(invocation: Invocation) -> HandlerResult:
    """Platform admin only: upload or replace a curated template's picture from FILE."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    file_path = _require_text_positional(invocation, "file", "image file path")
    _confirm(invocation, action=f"replace the picture of curated template '{slug}'", target=slug)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), slug=slug, file=file_path)
    return data, _meta(invocation, auth.workspace_id)


def support_template_inspect(invocation: Invocation) -> HandlerResult:
    """Platform admin only: read a template file (.zip) without importing it."""
    file_path = _require_text_positional(invocation, "file", "template file path")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file=file_path)
    return data, _meta(invocation, auth.workspace_id)


def support_template_import(invocation: Invocation) -> HandlerResult:
    """Platform admin only: import a template file (.zip) as a curated draft. '--yes' required."""
    file_path = _require_text_positional(invocation, "file", "template file path")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"file": file_path}
    _forward_optional(document, kwargs, ("dataset",))
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"import template file {file_path} into the curated catalog",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_template_snapshots(invocation: Invocation) -> HandlerResult:
    """Platform admin only: list every stored dataset the template catalog holds."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_template_audit(invocation: Invocation) -> HandlerResult:
    """Platform admin only: re-run every curated-catalog gate (read-only)."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_template_export(invocation: Invocation) -> HandlerResult:
    """Platform admin only: download a curated template as a .zip template file."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"slug": slug}
    _forward_optional(document, kwargs, ("output_path", "with_data"))
    refuse_existing_file(invocation, kwargs.get("output_path") or f"{kwargs['slug']}.zip")
    with open_service(invocation) as (service, auth):
        path = service.call(_symbol(invocation), **kwargs)
    return {"output_path": str(path)}, _meta(invocation, auth.workspace_id)


def support_template_export_dashboard(invocation: Invocation) -> HandlerResult:
    """Platform admin only: download a dashboard you can edit as a .zip template file."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {
        "dashboard_id": dashboard_id,
        "slug": _require_field(document, "slug"),
    }
    _forward_optional(document, kwargs, ("output_path", "with_data"))
    refuse_existing_file(invocation, kwargs.get("output_path") or f"{kwargs['slug']}.zip")
    with open_service(invocation) as (service, auth):
        path = service.call(_symbol(invocation), **kwargs)
    return {"output_path": str(path)}, _meta(invocation, auth.workspace_id)


# -- Admin console: billing actions, deals, partners, identities, archive -------------------


def _admin_ids(invocation: Invocation, ids: tuple[str, ...]) -> dict[str, int]:
    """Read the command's leading integer positionals by name."""
    found: dict[str, int] = {}
    for name in ids:
        raw = invocation.positional(name)
        human = name.removesuffix("_id").replace("_", " ") + " id"
        if raw is None:
            raise CliError(
                code=CODE_MISSING_ARGUMENT,
                message=f"This command requires a {human} argument.",
                exit_status=EXIT_USAGE,
                hint=f"Pass the {human} as a positional argument.",
            )
        try:
            found[name] = int(raw)
        except ValueError as exc:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"The {human} argument '{raw}' is not an integer.",
                exit_status=EXIT_USAGE,
            ) from exc
        if found[name] <= 0:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"The {human} argument '{raw}' must be a positive integer.",
                exit_status=EXIT_USAGE,
            )
    return found


def _admin_call(
    invocation: Invocation,
    *,
    ids: tuple[str, ...] = (),
    required: tuple[str, ...] = (),
    action: str | Callable[[dict[str, Any]], str] | None = None,
    target: str | None = None,
) -> HandlerResult:
    """Run one admin-console SDK method: positional ids, ``--input`` fields, confirmation.

    ``ids`` are the integer positionals, in order; the first one is the confirmation target
    unless ``target`` names another id. ``required`` are ``--input`` fields the SDK method
    takes without a default. ``action`` is the confirmation text (``{name}`` fills an id), or
    a function of the call's arguments for text that depends on them; a command without one
    is a read.
    """
    kwargs: dict[str, Any] = _admin_ids(invocation, ids)
    document = _bound_document(invocation)
    for field in required:
        kwargs[field] = _require_field(document, field)
    for field, value in document.items():
        if field not in kwargs:
            kwargs[field] = value
    if action is not None:
        text = action(kwargs) if callable(action) else action.format(**kwargs)
        _confirm(invocation, action=text, target=str(kwargs[target or ids[0]]))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_deal_create(invocation: Invocation) -> HandlerResult:
    """Create a deal on a workspace (positional id) or on a new one (`workspace_create`)."""
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"base_plan_id": _require_field(document, "base_plan_id")}
    kwargs.update({k: v for k, v in document.items() if k != "base_plan_id"})
    if invocation.positional("workspace_id") is not None:
        kwargs["workspace_id"] = _admin_ids(invocation, ("workspace_id",))["workspace_id"]
    created = kwargs.get("workspace_create")
    if kwargs.get("workspace_id") is not None:
        target = str(kwargs["workspace_id"])
    elif isinstance(created, dict) and created.get("name"):
        target = str(created["name"])
    else:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A deal needs a workspace: pass a workspace id or a workspace_create name.",
            exit_status=EXIT_USAGE,
            hint=(
                "Pass the workspace id as a positional argument, or "
                '\'workspace_create\': {"name": ..., "user_email": ...} in --input.'
            ),
        )
    _confirm(invocation, action=f"create a deal for {target}", target=target)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_partner_create(invocation: Invocation) -> HandlerResult:
    """Create a partner. Name comes from a positional or the ``name`` field."""
    document = _bound_document(invocation)
    name = _require_positional_or_field(invocation, document, "name", "partner name")
    kwargs: dict[str, Any] = {"name": name}
    _forward_optional(document, kwargs, ("name",))
    _confirm(invocation, action=f"create partner '{name}'", target=name)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_search(invocation: Invocation) -> HandlerResult:
    """Search workspaces, partners and users. The text is a positional or `q`."""
    document = _bound_document(invocation)
    text = _string_positional(invocation) or document.get("q")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **({"q": text} if text else {}))
    return data, _meta(invocation, auth.workspace_id)


def _refund_action(kwargs: dict[str, Any]) -> str:
    """Confirmation text for a refund; refuse both-or-neither of ``amount`` and ``full``."""
    amount = kwargs.get("amount")
    full = kwargs.get("full") is True
    if (amount is not None) == full:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="A refund needs exactly one of 'amount' (cents) or 'full': true.",
            exit_status=EXIT_USAGE,
            hint=(
                "Pass --input '{\"amount\": 500}' for a partial refund in cents, or "
                "--input '{\"full\": true}' to refund the whole payment."
            ),
        )
    if amount is not None and (
        not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0
    ):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The refund 'amount' must be a positive whole number of cents.",
            exit_status=EXIT_USAGE,
        )
    how = "the FULL last payment" if full else f"{amount} cents of the last payment"
    return f"refund {how} of workspace {kwargs['workspace_id']} (irreversible)"


def support_billing_start_trial(invocation: Invocation) -> HandlerResult:
    """Start a trial on a workspace. Workspace id is positional; `days` (1-60) is optional."""
    return _admin_call(
        invocation,
        ids=("workspace_id",),
        action=(
            "start a trial on workspace {workspace_id}: this REPLACES its billing and "
            "cancels a live paid Stripe subscription"
        ),
    )


def support_billing_end_trial(invocation: Invocation) -> HandlerResult:
    """End a workspace's trial now and charge the plan. Workspace id is positional."""
    return _admin_call(
        invocation,
        ids=("workspace_id",),
        action="end the trial on workspace {workspace_id}",
    )


def support_billing_retry_payment(invocation: Invocation) -> HandlerResult:
    """Retry a workspace's failed payment. Workspace id is positional."""
    return _admin_call(
        invocation,
        ids=("workspace_id",),
        action="retry the failed payment on workspace {workspace_id}",
    )


def support_billing_refund(invocation: Invocation) -> HandlerResult:
    """Refund a workspace's last payment: `amount` (cents) of it, or all of it with `full`."""
    return _admin_call(
        invocation,
        ids=("workspace_id",),
        action=_refund_action,
    )


def support_billing_change_plan(invocation: Invocation) -> HandlerResult:
    """Move a workspace to another plan. Workspace id and new plan id are positional."""
    return _admin_call(
        invocation,
        ids=("workspace_id", "new_plan_id"),
        action="change the plan of workspace {workspace_id}",
    )


def support_billing_cancel_subscription(invocation: Invocation) -> HandlerResult:
    """Cancel a workspace's subscription (`when`: now or period_end). Workspace id is positional."""
    return _admin_call(
        invocation,
        ids=("workspace_id",),
        required=("when",),
        action="cancel the subscription of workspace {workspace_id}",
    )


def support_connector_bucket_impact(invocation: Invocation) -> HandlerResult:
    """Show which plans a connector's bucket change would reach. Connector id is positional."""
    return _admin_call(invocation, ids=("connector_id",))


def support_entitlement_registry(invocation: Invocation) -> HandlerResult:
    """List the entitlement registry: every entitlement key a plan or deal can set."""
    return _admin_call(invocation)


def support_plan_catalog(invocation: Invocation) -> HandlerResult:
    """List the plans catalog with the entitlement values each plan carries."""
    return _admin_call(invocation)


def support_deal_list(invocation: Invocation) -> HandlerResult:
    """List all deals."""
    return _admin_call(invocation)


def support_deal_get(invocation: Invocation) -> HandlerResult:
    """Get one deal by id."""
    return _admin_call(invocation, ids=("deal_id",))


def _deal_update_action(kwargs: dict[str, Any]) -> str:
    """Confirmation text for a deal update; a cancellation says so."""
    if kwargs.get("status") == "cancelled":
        return f"CANCEL deal {kwargs['deal_id']} (status=cancelled ends the deal)"
    return f"update deal {kwargs['deal_id']}"


def support_deal_update(invocation: Invocation) -> HandlerResult:
    """Update a deal's terms or status. Deal id is positional; the changes come from `--input`."""
    return _admin_call(invocation, ids=("deal_id",), action=_deal_update_action)


def support_deal_activity(invocation: Invocation) -> HandlerResult:
    """List a deal's activity log."""
    return _admin_call(invocation, ids=("deal_id",))


def support_deal_preview_entitlement(invocation: Invocation) -> HandlerResult:
    """Preview the entitlements a deal grants, without changing anything."""
    return _admin_call(invocation, ids=("deal_id",))


def support_deal_opt_in(invocation: Invocation) -> HandlerResult:
    """Release a deal's opt-in rollout pins (`keys`, `connectors` or `everything`)."""
    return _admin_call(
        invocation,
        ids=("deal_id",),
        action="release opt-in rollout pins on deal {deal_id}",
    )


def _move_to_partner_action(kwargs: dict[str, Any]) -> str:
    """Confirmation text for a move; ``when=now`` cancels the subscription and refunds."""
    base = f"move deal {kwargs['deal_id']} to partner {kwargs['partner_id']}"
    if kwargs.get("when") == "now":
        return (
            f"{base} NOW: cancels the workspace's subscription prorated "
            "and refunds the unused time"
        )
    return f"{base} at period end"


def support_deal_move_to_partner(invocation: Invocation) -> HandlerResult:
    """Schedule a direct deal to move under a partner. Deal and partner ids are positional."""
    return _admin_call(
        invocation,
        ids=("deal_id", "partner_id"),
        required=("price", "billing_interval"),
        action=_move_to_partner_action,
    )


def support_deal_cancel_move_to_partner(invocation: Invocation) -> HandlerResult:
    """Cancel a deal's pending move to a partner. Deal id is positional."""
    return _admin_call(
        invocation,
        ids=("deal_id",),
        action="cancel the pending partner move of deal {deal_id}",
    )


def support_identity_list(invocation: Invocation) -> HandlerResult:
    """List identities (users across workspaces)."""
    return _admin_call(invocation)


def support_identity_get(invocation: Invocation) -> HandlerResult:
    """Get one identity by user id."""
    return _admin_call(invocation, ids=("user_id",))


def support_partner_list(invocation: Invocation) -> HandlerResult:
    """List all partners."""
    return _admin_call(invocation)


def support_partner_get(invocation: Invocation) -> HandlerResult:
    """Get one partner by id."""
    return _admin_call(invocation, ids=("partner_id",))


def support_partner_update(invocation: Invocation) -> HandlerResult:
    """Update a partner. Partner id is positional; the changes come from `--input`."""
    return _admin_call(invocation, ids=("partner_id",), action="update partner {partner_id}")


def support_partner_activity(invocation: Invocation) -> HandlerResult:
    """List a partner's activity log."""
    return _admin_call(invocation, ids=("partner_id",))


def support_partner_billing(invocation: Invocation) -> HandlerResult:
    """Show a partner's billing summary."""
    return _admin_call(invocation, ids=("partner_id",))


def support_partner_invoices(invocation: Invocation) -> HandlerResult:
    """List a partner's invoices."""
    return _admin_call(invocation, ids=("partner_id",))


def support_partner_charge_invoices(invocation: Invocation) -> HandlerResult:
    """Charge a partner's open invoices now. Partner id is positional."""
    return _admin_call(
        invocation,
        ids=("partner_id",),
        action="charge the open invoices of partner {partner_id}",
    )


def support_partner_send_payment_link(invocation: Invocation) -> HandlerResult:
    """Email a partner its payment link. Partner id is positional."""
    return _admin_call(
        invocation,
        ids=("partner_id",),
        action="email the payment link of partner {partner_id}",
    )


def support_partner_client_list(invocation: Invocation) -> HandlerResult:
    """List a partner's client workspaces."""
    return _admin_call(invocation, ids=("partner_id",))


def support_partner_client_delete(invocation: Invocation) -> HandlerResult:
    """Delete a client workspace of a partner. Partner id and workspace id are positional."""
    return _admin_call(
        invocation,
        ids=("partner_id", "workspace_id"),
        action="delete client workspace {workspace_id} of partner {partner_id} (irreversible)",
        target="workspace_id",
    )


def support_partner_client_detach(invocation: Invocation) -> HandlerResult:
    """Detach a partner client workspace into a direct deal. Both ids are positional."""
    return _admin_call(
        invocation,
        ids=("partner_id", "workspace_id"),
        required=("price", "contact_email"),
        action="detach client workspace {workspace_id} from partner {partner_id}",
        target="workspace_id",
    )


def support_partner_client_cancel_detach(invocation: Invocation) -> HandlerResult:
    """Cancel a client workspace's pending detach. Partner id and workspace id are positional."""
    return _admin_call(
        invocation,
        ids=("partner_id", "workspace_id"),
        action="cancel the pending detach of workspace {workspace_id} from partner {partner_id}",
        target="workspace_id",
    )


def support_triage(invocation: Invocation) -> HandlerResult:
    """Show the triage queue: what needs attention."""
    return _admin_call(invocation)


def support_usage_tiles(invocation: Invocation) -> HandlerResult:
    """Show the usage tiles."""
    return _admin_call(invocation)


def support_workspace_activity(invocation: Invocation) -> HandlerResult:
    """List a workspace's activity log."""
    return _admin_call(invocation, ids=("workspace_id",))


def support_workspace_entitlement(invocation: Invocation) -> HandlerResult:
    """Show the entitlements a workspace resolves to."""
    return _admin_call(invocation, ids=("workspace_id",))


def support_workspace_deal_seed(invocation: Invocation) -> HandlerResult:
    """Show the deal terms a workspace's current subscription would seed."""
    return _admin_call(invocation, ids=("workspace_id",))


def support_workspace_chargebee_cancelled(invocation: Invocation) -> HandlerResult:
    """Record a workspace's Chargebee subscription as cancelled. Workspace id is positional."""
    return _admin_call(
        invocation,
        ids=("workspace_id",),
        action="mark workspace {workspace_id} as cancelled in Chargebee",
    )


def support_workspace_archive_info(invocation: Invocation) -> HandlerResult:
    """Show what archiving a workspace would do, and its archive state."""
    return _admin_call(invocation, ids=("workspace_id",))


def support_workspace_archive(invocation: Invocation) -> HandlerResult:
    """Archive a workspace to cold storage. `confirm_name` must be the workspace's name."""
    return _admin_call(
        invocation,
        ids=("workspace_id",),
        required=("storage_class", "confirm_name"),
        action="archive workspace {workspace_id}",
    )


def support_workspace_restore_archive(invocation: Invocation) -> HandlerResult:
    """Restore an archived workspace from cold storage. Workspace id is positional."""
    return _admin_call(
        invocation,
        ids=("workspace_id",),
        action="restore archived workspace {workspace_id}",
    )


def support_workspace_invite_cancel(invocation: Invocation) -> HandlerResult:
    """Cancel a pending workspace invite. Workspace id and invite id are positional."""
    return _admin_call(
        invocation,
        ids=("workspace_id", "invite_id"),
        action="cancel invite {invite_id} to workspace {workspace_id}",
    )


def support_workspace_invite_resend(invocation: Invocation) -> HandlerResult:
    """Resend a pending workspace invite. Workspace id and invite id are positional."""
    return _admin_call(
        invocation,
        ids=("workspace_id", "invite_id"),
        action="resend invite {invite_id} to workspace {workspace_id}",
    )
