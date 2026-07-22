"""Billing API client for managing workspace subscriptions and invoices in Mammoth.

Covers Chargebee plan lookup, Stripe subscription lifecycle (create, cancel,
retry, sync, usage, status), payment methods, invoices, and hosted/checkout/
portal URL generation. This is a thin typed wrapper over the REST endpoints —
no confirmation prompts or business logic live here; that belongs to callers
(e.g. the CLI).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

_list = list  # Alias to avoid shadowing by method name

# ── Validation error constants ────────────────────────────────────────────────

ERR_INVOICE_ID_POSITIVE = "`invoice_id` must be a positive integer, got {0}."
ERR_PLAN_ID_POSITIVE = "`plan_id` must be a positive integer, got {0}."
ERR_PAYMENT_METHOD_ID_EMPTY = "`payment_method_id` must be a non-empty string."
ERR_OBJECT_TYPE_EMPTY = "`object_type` must be a non-empty string."
ERR_SUCCESS_URL_EMPTY = "`success_url` must be a non-empty string."
ERR_CANCEL_URL_EMPTY = "`cancel_url` must be a non-empty string."
ERR_SUBSCRIPTION_PATCH_EMPTY = "`patch` must be a non-empty list of patch operations."


class BillingAPI:
    """Client for workspace billing operations (Chargebee + Stripe).

    Access via ``client.billing``::

        plan = client.billing.chargebee_plan()
        subscription = client.billing.stripe_get()
        invoices = client.billing.invoice_list()
        client.billing.stripe_payment_method_set_default("pm_123")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    # ── Chargebee ──────────────────────────────────────────────────────────

    def chargebee_plan(self) -> dict[str, Any]:
        """Get the workspace's current Chargebee plan.

        Returns:
            Dict with Chargebee plan details.
        """
        return self._client._request_json("GET", f"/workspaces/{self._ws()}/chargebee-plan")

    # ── Hosted / checkout / portal URLs ──────────────────────────────────────

    def hosted_page(self, object_type: str, plan_id: str | None = None) -> dict[str, Any]:
        """Fetch a Chargebee hosted page URL (e.g. change-plan flow).

        Args:
            object_type: Type of hosted page to generate (e.g. ``"change_plan"``).
            plan_id: Optional plan ID to preselect on the hosted page.

        Returns:
            Dict with the hosted page URL.

        Raises:
            MammothValidationError: If ``object_type`` is empty.
        """
        if not object_type:
            raise MammothValidationError(ERR_OBJECT_TYPE_EMPTY)
        body: dict[str, Any] = {"object_type": object_type}
        if plan_id is not None:
            body["plan_id"] = plan_id
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/subscription_v1/hosted-page",
            json=body,
        )

    def stripe_checkout_url(
        self,
        success_url: str,
        cancel_url: str,
        add_payment_method_only: bool | None = None,
    ) -> dict[str, Any]:
        """Create a Stripe checkout URL for the workspace.

        Args:
            success_url: URL to redirect to on successful checkout.
            cancel_url: URL to redirect to if checkout is cancelled.
            add_payment_method_only: If ``True``, only collect a payment
                method without starting a subscription.

        Returns:
            Dict with the checkout URL.

        Raises:
            MammothValidationError: If ``success_url`` or ``cancel_url`` is empty.
        """
        if not success_url:
            raise MammothValidationError(ERR_SUCCESS_URL_EMPTY)
        if not cancel_url:
            raise MammothValidationError(ERR_CANCEL_URL_EMPTY)
        body: dict[str, Any] = {"success_url": success_url, "cancel_url": cancel_url}
        if add_payment_method_only is not None:
            body["add_payment_method_only"] = add_payment_method_only
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/subscription/create-checkout",
            json=body,
        )

    def stripe_portal_url(self, return_url: str | None = None) -> dict[str, Any]:
        """Create a Stripe customer portal URL for the workspace.

        Args:
            return_url: Optional URL to return to after the portal session.

        Returns:
            Dict with the customer portal URL.
        """
        body: dict[str, Any] = {}
        if return_url is not None:
            body["return_url"] = return_url
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/subscription/customer-portal",
            json=body,
        )

    # ── Stripe subscription lifecycle ────────────────────────────────────────

    def stripe_get(self) -> dict[str, Any]:
        """Get the workspace's Stripe subscription.

        Returns:
            Dict with subscription details.
        """
        return self._client._request_json("GET", f"/workspaces/{self._ws()}/subscription")

    def stripe_create(self, plan_id: int, billing_interval: str | None = None) -> dict[str, Any]:
        """Create a new Stripe subscription for the workspace.

        Args:
            plan_id: ID of the plan to subscribe to (must be positive).
            billing_interval: Billing interval (e.g. ``"monthly"``, ``"yearly"``).
                Defaults to ``"monthly"`` server-side if omitted.

        Returns:
            Dict with created subscription info.

        Raises:
            MammothValidationError: If ``plan_id`` is not a positive integer.
        """
        if plan_id <= 0:
            raise MammothValidationError(ERR_PLAN_ID_POSITIVE.format(plan_id))
        body: dict[str, Any] = {"plan_id": plan_id}
        if billing_interval is not None:
            body["billing_interval"] = billing_interval
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/subscription",
            json=body,
        )

    def stripe_cancel(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Cancel the workspace's Stripe subscription.

        Args:
            body: Optional opaque request body (server accepts an object or
                ``null``).

        Returns:
            Dict with cancellation result.
        """
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/subscription/cancel",
            json=body,
        )

    def stripe_end_trial(self) -> dict[str, Any]:
        """End the workspace's trial and start its subscription immediately.

        Returns:
            Dict with the updated subscription info.
        """
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/subscription/end-trial"
        )

    def stripe_retry_payment(self) -> dict[str, Any]:
        """Retry the last failed payment for the workspace's subscription.

        Returns:
            Dict with the retry result.
        """
        return self._client._request_json(
            "POST", f"/workspaces/{self._ws()}/subscription/retry-payment"
        )

    def stripe_sync(self) -> dict[str, Any]:
        """Sync the workspace's subscription state from Stripe.

        Returns:
            Dict with the synced subscription info.
        """
        return self._client._request_json("POST", f"/workspaces/{self._ws()}/subscription/sync")

    def stripe_status(self) -> dict[str, Any]:
        """Get the workspace's Stripe subscription status.

        Returns:
            Dict with subscription status info.
        """
        return self._client._request_json("GET", f"/workspaces/{self._ws()}/subscription/status")

    def stripe_history(self) -> dict[str, Any]:
        """Get the workspace's Stripe billing history.

        Returns:
            Dict with billing history entries.
        """
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/subscription/billing-history"
        )

    def stripe_usage(self) -> dict[str, Any]:
        """Get the workspace's current usage against its subscription.

        Returns:
            Dict with usage details (e.g. storage, connectors, seats).
        """
        return self._client._request_json("GET", f"/workspaces/{self._ws()}/subscription/usage")

    def stripe_preview_invoice(
        self,
        connector_ids: str | None = None,
        additional_storage_gb: int | None = None,
        additional_user_seats: int | None = None,
    ) -> dict[str, Any]:
        """Preview the invoice for a hypothetical subscription change.

        Args:
            connector_ids: Comma-separated connector IDs to preview adding.
            additional_storage_gb: Additional storage (GB) to preview adding.
            additional_user_seats: Additional user seats to preview adding.

        Returns:
            Dict with the previewed invoice.
        """
        params: dict[str, Any] = {}
        if connector_ids is not None:
            params["connector_ids"] = connector_ids
        if additional_storage_gb is not None:
            params["additional_storage_gb"] = additional_storage_gb
        if additional_user_seats is not None:
            params["additional_user_seats"] = additional_user_seats
        return self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/subscription/preview-invoice",
            params=params or None,
        )

    def stripe_upcoming_invoice(self) -> dict[str, Any]:
        """Get the workspace's upcoming invoice.

        Returns:
            Dict with the upcoming invoice.
        """
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/subscription/upcoming-invoice"
        )

    # ── Payment methods ───────────────────────────────────────────────────

    def stripe_payment_method_list(self) -> dict[str, Any]:
        """List the workspace's Stripe payment methods.

        Returns:
            Dict with the payment methods list.
        """
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/subscription/payment-methods"
        )

    def stripe_payment_method_set_default(self, payment_method_id: str) -> dict[str, Any]:
        """Set the default Stripe payment method for the workspace.

        Args:
            payment_method_id: Non-empty Stripe payment method ID.

        Returns:
            Dict with the updated payment method info.

        Raises:
            MammothValidationError: If ``payment_method_id`` is empty.
        """
        if not payment_method_id:
            raise MammothValidationError(ERR_PAYMENT_METHOD_ID_EMPTY)
        return self._client._request_json(
            "POST",
            f"/workspaces/{self._ws()}/subscription/payment-methods/default",
            json={"payment_method_id": payment_method_id},
        )

    def stripe_payment_method_delete(self, payment_method_id: str) -> dict[str, Any]:
        """Delete a Stripe payment method from the workspace.

        Args:
            payment_method_id: Non-empty Stripe payment method ID.

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If ``payment_method_id`` is empty.
        """
        if not payment_method_id:
            raise MammothValidationError(ERR_PAYMENT_METHOD_ID_EMPTY)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{self._ws()}/subscription/payment-methods/{payment_method_id}",
        )

    # ── Invoices ──────────────────────────────────────────────────────────

    def invoice_list(self, limit: int | None = None, sort: str | None = None) -> dict[str, Any]:
        """List the workspace's invoices.

        Args:
            limit: Maximum number of results to return (server default 50, max 100).
            sort: Sort spec, e.g. ``"(date:desc)"`` (allowed fields: ``date``,
                ``updated_at``).

        Returns:
            Dict with the invoices list.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if sort is not None:
            params["sort"] = sort
        return self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/subscription_v1/invoices",
            params=params or None,
        )

    def invoice_get(self, invoice_id: int) -> dict[str, Any]:
        """Get details of a specific invoice.

        Args:
            invoice_id: ID of the invoice (must be positive).

        Returns:
            Dict with invoice details.

        Raises:
            MammothValidationError: If ``invoice_id`` is not a positive integer.
        """
        if invoice_id <= 0:
            raise MammothValidationError(ERR_INVOICE_ID_POSITIVE.format(invoice_id))
        return self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/subscription_v1/invoices/{invoice_id}",
        )

    def invoice_charge(self) -> dict[str, Any]:
        """Trigger an immediate charge of the workspace's outstanding invoices.

        Returns:
            Dict with the charge result.
        """
        return self._client._request_json("POST", f"/workspaces/{self._ws()}/invoices/charge")

    # ── Subscription detail (v1) ─────────────────────────────────────────────

    def subscription_get(self, fields: str | None = None) -> dict[str, Any]:
        """Get the workspace's subscription detail.

        Args:
            fields: Comma-separated fields to return (e.g. ``"id,name"``).
                Server default returns the standard field set.

        Returns:
            Dict with subscription detail.
        """
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        return self._client._request_json(
            "GET",
            f"/workspaces/{self._ws()}/subscription_v1",
            params=params or None,
        )

    def subscription_update(self, patch: _list[dict[str, Any]]) -> dict[str, Any]:
        """Update the workspace's subscription via JSON-patch operations.

        The backend expects ``{"patch": [<ops>]}``. Each op has:

        - ``op``: one of ``"add"``, ``"remove"``, ``"replace"``.
        - ``path``: ``"addons"`` (the only supported path).
        - ``value``: an addon spec dict, shape depends on addon type, e.g.
          ``{"type": "storage", "count": 1}`` or
          ``{"type": "connector", "add": ["ga_lib"], "remove": ["facebook_ads"]}``.

        Args:
            patch: Non-empty list of raw patch operation dicts.

        Returns:
            Dict with the updated subscription detail.

        Raises:
            MammothValidationError: If ``patch`` is empty.
        """
        if not patch:
            raise MammothValidationError(ERR_SUBSCRIPTION_PATCH_EMPTY)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{self._ws()}/subscription_v1",
            json={"patch": patch},
        )
