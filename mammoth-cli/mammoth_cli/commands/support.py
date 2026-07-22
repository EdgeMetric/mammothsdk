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

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_CONFIRM_TARGET, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code="sdk_symbol_unresolved",
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


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
            code="invalid_argument",
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument parsed as an int, or raise usage."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code="missing_argument",
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
            code="missing_argument",
            message=f"A {human} is required.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {human} as a positional argument or a '{field}' input field.",
        )
    return str(value)


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code="missing_field",
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy any present optional fields from the input document into kwargs."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


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
    """List all subscription connectors. Confirm target: the auth workspace id."""
    with open_service(invocation) as (service, auth):
        _confirm(invocation, action="list connectors", target=str(auth.workspace_id))
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_connector_create(invocation: Invocation) -> HandlerResult:
    """Create a connector. Name comes from a positional or the ``name`` field."""
    document = invocation.load_input() or {}
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
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"connector_id": connector_id}
    _forward_optional(document, kwargs, ("name", "description", "price_per_month", "enabled"))
    _confirm(
        invocation, action=f"update connector {connector_id}", target=str(connector_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_connector_delete(invocation: Invocation) -> HandlerResult:
    """Delete one connector by id."""
    connector_id = _require_int_positional(invocation, "connector id")
    _confirm(
        invocation, action=f"delete connector {connector_id}", target=str(connector_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), connector_id=connector_id)
    return data, _meta(invocation, auth.workspace_id)


# -- Connector profiles ---------------------------------------------------------


def support_connector_profile_list(invocation: Invocation) -> HandlerResult:
    """List all connector profiles. Confirm target: the auth workspace id."""
    with open_service(invocation) as (service, auth):
        _confirm(invocation, action="list connector profiles", target=str(auth.workspace_id))
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_connector_profile_create(invocation: Invocation) -> HandlerResult:
    """Create a connector profile. Name comes from a positional or ``name`` field."""
    document = invocation.load_input() or {}
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
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"profile_id": profile_id}
    _forward_optional(document, kwargs, ("name", "description", "connectors"))
    _confirm(
        invocation, action=f"update connector profile {profile_id}", target=str(profile_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_connector_profile_delete(invocation: Invocation) -> HandlerResult:
    """Delete one connector profile by id."""
    profile_id = _require_int_positional(invocation, "profile id")
    _confirm(
        invocation, action=f"delete connector profile {profile_id}", target=str(profile_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), profile_id=profile_id)
    return data, _meta(invocation, auth.workspace_id)


def support_connector_profile_add_connector(invocation: Invocation) -> HandlerResult:
    """Add a connector to a connector profile. Profile id is positional."""
    profile_id = _require_int_positional(invocation, "profile id")
    document = invocation.load_input()
    connector_id = _require_field(document, "connector_id")
    kwargs: dict[str, Any] = {"profile_id": profile_id, "connector_id": connector_id}
    assert document is not None
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
    """List all subscription features. Confirm target: the auth workspace id."""
    with open_service(invocation) as (service, auth):
        _confirm(invocation, action="list features", target=str(auth.workspace_id))
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_feature_create(invocation: Invocation) -> HandlerResult:
    """Create a feature. Name comes from a positional or the ``name`` field."""
    document = invocation.load_input() or {}
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
    document = invocation.load_input() or {}
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
    """List all feature profiles. Confirm target: the auth workspace id."""
    with open_service(invocation) as (service, auth):
        _confirm(invocation, action="list feature profiles", target=str(auth.workspace_id))
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_feature_profile_create(invocation: Invocation) -> HandlerResult:
    """Create a feature profile. Name comes from a positional or ``name`` field."""
    document = invocation.load_input() or {}
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
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"profile_id": profile_id}
    _forward_optional(document, kwargs, ("name", "description", "features"))
    _confirm(
        invocation, action=f"update feature profile {profile_id}", target=str(profile_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_feature_profile_delete(invocation: Invocation) -> HandlerResult:
    """Delete one feature profile by id."""
    profile_id = _require_int_positional(invocation, "profile id")
    _confirm(
        invocation, action=f"delete feature profile {profile_id}", target=str(profile_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), profile_id=profile_id)
    return data, _meta(invocation, auth.workspace_id)


def support_feature_profile_add_feature(invocation: Invocation) -> HandlerResult:
    """Add a feature to a feature profile. Profile id is positional."""
    profile_id = _require_int_positional(invocation, "profile id")
    document = invocation.load_input()
    feature_id = _require_field(document, "feature_id")
    kwargs: dict[str, Any] = {"profile_id": profile_id, "feature_id": feature_id}
    assert document is not None
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
    document = invocation.load_input()
    user_id = _require_field(document, "user_id")
    kwargs: dict[str, Any] = {"workspace_id": workspace_id, "user_id": user_id}
    assert document is not None
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
    """List all subscription plans. Confirm target: the auth workspace id."""
    with open_service(invocation) as (service, auth):
        _confirm(invocation, action="list plans", target=str(auth.workspace_id))
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_plan_self_serve_list(invocation: Invocation) -> HandlerResult:
    """List self-serve subscription plans. Confirm target: the auth workspace id."""
    with open_service(invocation) as (service, auth):
        _confirm(invocation, action="list self-serve plans", target=str(auth.workspace_id))
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_plan_chargebee_list(invocation: Invocation) -> HandlerResult:
    """List available Chargebee plans/resources. Confirm target: the auth workspace id."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("resource",))
    with open_service(invocation) as (service, auth):
        _confirm(invocation, action="list chargebee plans", target=str(auth.workspace_id))
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_get(invocation: Invocation) -> HandlerResult:
    """Get one subscription plan by id."""
    plan_id = _require_int_positional(invocation, "plan id")
    _confirm(invocation, action=f"get plan {plan_id}", target=str(plan_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id)
    return data, _meta(invocation, auth.workspace_id)


def support_plan_create(invocation: Invocation) -> HandlerResult:
    """Create a subscription plan. Name is positional; required fields from ``--input``."""
    document = invocation.load_input() or {}
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
    document = invocation.load_input() or {}
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
    document = invocation.load_input()
    storage_tiers = _require_field(document, "storage_tiers")
    _confirm(
        invocation, action=f"update storage tiers for plan {plan_id}", target=str(plan_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), plan_id=plan_id, storage_tiers=storage_tiers
        )
    return data, _meta(invocation, auth.workspace_id)


def support_plan_archive(invocation: Invocation) -> HandlerResult:
    """Archive one subscription plan by id."""
    plan_id = _require_int_positional(invocation, "plan id")
    _confirm(invocation, action=f"archive plan {plan_id}", target=str(plan_id))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), plan_id=plan_id)
    return data, _meta(invocation, auth.workspace_id)


# -- Subscriptions ------------------------------------------------------------------


def support_subscription_get(invocation: Invocation) -> HandlerResult:
    """Get a workspace's Chargebee subscription details. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"workspace_id": workspace_id}
    _forward_optional(document, kwargs, ("fields",))
    _confirm(
        invocation,
        action=f"get subscription for workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_subscription_create(invocation: Invocation) -> HandlerResult:
    """Register a workspace's Chargebee subscription. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = invocation.load_input()
    plan_id = _require_field(document, "plan_id")
    kwargs: dict[str, Any] = {"workspace_id": workspace_id, "plan_id": plan_id}
    assert document is not None
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
    document = invocation.load_input()
    subscription_id = _require_field(document, "subscription_id")
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
    """List users across workspaces. Confirm target: the auth workspace id."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("fields", "sort", "offset", "limit"))
    with open_service(invocation) as (service, auth):
        _confirm(
            invocation, action="list users across workspaces", target=str(auth.workspace_id)
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_user_register(invocation: Invocation) -> HandlerResult:
    """Register a new user. Email is positional; required fields from ``--input``."""
    document = invocation.load_input() or {}
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
    document = invocation.load_input() or {}
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
        _confirm(invocation, action="list workspaces", target=str(auth.workspace_id))
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_get(invocation: Invocation) -> HandlerResult:
    """Get details of a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"workspace_id": workspace_id}
    _forward_optional(document, kwargs, ("fields",))
    _confirm(
        invocation, action=f"get workspace {workspace_id}", target=str(workspace_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_create(invocation: Invocation) -> HandlerResult:
    """Create a workspace. Name is positional; required fields from ``--input``."""
    document = invocation.load_input() or {}
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
    document = invocation.load_input()
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
    _confirm(
        invocation, action=f"update workspace {workspace_id}", target=str(workspace_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_delete(invocation: Invocation) -> HandlerResult:
    """Delete one workspace by id."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    _confirm(
        invocation, action=f"delete workspace {workspace_id}", target=str(workspace_id)
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), workspace_id=workspace_id)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_suspend_access(invocation: Invocation) -> HandlerResult:
    """Suspend user access to a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = invocation.load_input() or {}
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
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"workspace_id": workspace_id}
    _forward_optional(document, kwargs, ("limit", "offset", "fields", "sort"))
    _confirm(
        invocation,
        action=f"list users in workspace {workspace_id}",
        target=str(workspace_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_workspace_user_add(invocation: Invocation) -> HandlerResult:
    """Add a user to a workspace. Workspace id is positional."""
    workspace_id = _require_int_positional(invocation, "workspace id")
    document = invocation.load_input()
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
    document = invocation.load_input()
    user_id = _require_field(document, "user_id")
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
    document = invocation.load_input()
    user_id = _require_field(document, "user_id")
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
