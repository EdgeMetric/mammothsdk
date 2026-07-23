"""Handlers for the ``billing`` command family (workspace-scoped).

Billing operations act on the current workspace's Chargebee/Stripe billing
state and financial records, so every command in this family carries the
manifest's ``confirm_target`` policy: the caller must pass ``--yes`` and an
exact ``--confirm TARGET`` before the underlying SDK call is made, even for
read-only lookups. The target is the specific resource id when one exists
(an invoice id or a payment method id); otherwise it is the resolved
workspace id, since the action affects the workspace's overall billing
state. Handlers dispatch through the generic
:meth:`~mammoth_cli.services.protocol.MammothService.call` seam to the public
SDK method named by the command's reviewed manifest ``sdk_symbol``.
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
from mammoth_cli.runtime.confirm import POLICY_CONFIRM_TARGET, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service

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


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent."""
    return invocation.extra_args[0] if invocation.extra_args else None


def _require_string_positional(invocation: Invocation, name: str) -> str:
    """Return the first positional argument, or raise ``missing_argument``."""
    value = _string_positional(invocation)
    if not value:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


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
    """Return the first positional argument as an int, or raise ``missing_argument``."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


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
    """Copy any of ``fields`` present in ``document`` into ``kwargs``."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a billing command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def billing_chargebee_plan(invocation: Invocation) -> HandlerResult:
    """Get the workspace's Chargebee plan details. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"view the Chargebee plan for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_hosted_page(invocation: Invocation) -> HandlerResult:
    """Get a Chargebee hosted-page URL. Object type is positional or an input field."""
    document = invocation.load_input() or {}
    object_type = _string_positional(invocation) or document.get("object_type")
    if not object_type:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A hosted-page object type is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the object type as a positional argument or an 'object_type' input field.",
        )
    kwargs: dict[str, Any] = {"object_type": object_type}
    _forward_optional(document, kwargs, ("plan_id",))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"request a hosted page for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_invoice_charge(invocation: Invocation) -> HandlerResult:
    """Charge the workspace's outstanding invoice. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"charge the invoice for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_invoice_get(invocation: Invocation) -> HandlerResult:
    """Get one invoice by id. ``--yes --confirm INVOICE_ID`` required."""
    invoice_id = _require_int_positional(invocation, "invoice id")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"view invoice {invoice_id}",
        target=str(invoice_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), invoice_id=invoice_id)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_invoice_list(invocation: Invocation) -> HandlerResult:
    """List invoices for the workspace. ``--yes --confirm WS`` required."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("limit", "sort"))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"list invoices for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_cancel(invocation: Invocation) -> HandlerResult:
    """Cancel the workspace's Stripe subscription. ``--yes --confirm WS`` required."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("body",))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"cancel the Stripe subscription for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_checkout_url(invocation: Invocation) -> HandlerResult:
    """Get a Stripe Checkout URL. ``success_url``/``cancel_url`` come from ``--input``."""
    document = invocation.load_input()
    success_url = _require_field(document, "success_url")
    cancel_url = _require_field(document, "cancel_url")
    kwargs: dict[str, Any] = {"success_url": success_url, "cancel_url": cancel_url}
    assert document is not None
    _forward_optional(document, kwargs, ("add_payment_method_only",))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"create a Stripe checkout session for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_create(invocation: Invocation) -> HandlerResult:
    """Create a Stripe subscription. Plan id is positional; interval is optional."""
    plan_id = _require_int_positional(invocation, "plan id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"plan_id": plan_id}
    _forward_optional(document, kwargs, ("billing_interval",))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"create a Stripe subscription for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_end_trial(invocation: Invocation) -> HandlerResult:
    """End the workspace's Stripe trial. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"end the Stripe trial for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_get(invocation: Invocation) -> HandlerResult:
    """Get the workspace's Stripe billing state. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"view Stripe billing state for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_history(invocation: Invocation) -> HandlerResult:
    """Get the workspace's Stripe billing history. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"view Stripe billing history for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_payment_method_delete(invocation: Invocation) -> HandlerResult:
    """Delete a Stripe payment method. ``--yes --confirm PAYMENT_METHOD_ID`` required."""
    payment_method_id = _require_string_positional(invocation, "payment method id")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"delete payment method {payment_method_id}",
        target=payment_method_id,
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), payment_method_id=payment_method_id)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_payment_method_list(invocation: Invocation) -> HandlerResult:
    """List the workspace's Stripe payment methods. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"list Stripe payment methods for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_payment_method_set_default(invocation: Invocation) -> HandlerResult:
    """Set a Stripe payment method as default. ``--yes --confirm PAYMENT_METHOD_ID`` required."""
    payment_method_id = _require_string_positional(invocation, "payment method id")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"set payment method {payment_method_id} as default",
        target=payment_method_id,
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), payment_method_id=payment_method_id)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_portal_url(invocation: Invocation) -> HandlerResult:
    """Get a Stripe billing portal URL. ``--yes --confirm WS`` required."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("return_url",))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"request a Stripe billing portal URL for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_preview_invoice(invocation: Invocation) -> HandlerResult:
    """Preview the workspace's next Stripe invoice. ``--yes --confirm WS`` required."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(
        document, kwargs, ("connector_ids", "additional_storage_gb", "additional_user_seats")
    )
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"preview the Stripe invoice for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_retry_payment(invocation: Invocation) -> HandlerResult:
    """Retry the workspace's failed Stripe payment. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"retry the Stripe payment for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_status(invocation: Invocation) -> HandlerResult:
    """Get the workspace's Stripe subscription status. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"view Stripe status for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_sync(invocation: Invocation) -> HandlerResult:
    """Sync the workspace's Stripe billing state. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"sync Stripe billing state for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_upcoming_invoice(invocation: Invocation) -> HandlerResult:
    """Get the workspace's upcoming Stripe invoice. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"view the upcoming Stripe invoice for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_stripe_usage(invocation: Invocation) -> HandlerResult:
    """Get the workspace's Stripe usage figures. ``--yes --confirm WS`` required."""
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"view Stripe usage for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id, None)


def billing_subscription_get(invocation: Invocation) -> HandlerResult:
    """Get the workspace's subscription details. ``--yes --confirm WS`` required."""
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {}
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"view the subscription for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def billing_subscription_update(invocation: Invocation) -> HandlerResult:
    """Apply a patch to the workspace's subscription. ``patch`` comes from ``--input``."""
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"update the subscription for workspace {auth.workspace_id}",
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), patch=patch)
    return data, _meta(invocation, auth.workspace_id, None)
