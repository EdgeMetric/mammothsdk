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
    _forward_optional(document, kwargs, ("description", "price_per_month", "enabled"))
    _confirm(invocation, action=f"create connector '{name}'", target=name)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_connector_update(invocation: Invocation) -> HandlerResult:
    """Update a connector. Connector id is positional; fields come from ``--input``."""
    connector_id = _require_int_positional(invocation, "connector id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"connector_id": connector_id}
    _forward_optional(document, kwargs, ("name", "description", "price_per_month", "enabled"))
    _confirm(invocation, action=f"update connector {connector_id}", target=str(connector_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


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
    with open_service(invocation) as (service, auth):
        path = service.call(_symbol(invocation), **kwargs)
    return {"output_path": str(path)}, _meta(invocation, auth.workspace_id)
