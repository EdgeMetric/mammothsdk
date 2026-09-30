"""Unit tests for the BillingAPI client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.billing import BillingAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[BillingAPI, MagicMock]:
    """Create a BillingAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    api = BillingAPI(mock_client)
    return api, mock_client


class TestChargebeePlan:
    async def test_chargebee_plan(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"plan_id": "internal"})
        result = await api.chargebee_plan()
        mock_client._request_json.assert_called_once_with("GET", "/workspaces/2/chargebee-plan")
        assert result == {"plan_id": "internal"}


class TestHostedPage:
    async def test_hosted_page_minimal(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"url": "https://example.com"})
        await api.hosted_page("change_plan")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/subscription_v1/hosted-page",
            json={"object_type": "change_plan"},
        )

    async def test_hosted_page_with_plan_id(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"url": "https://example.com"})
        await api.hosted_page("change_plan", plan_id="test_plan_11")
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json == {"object_type": "change_plan", "plan_id": "test_plan_11"}

    async def test_hosted_page_empty_object_type_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="object_type"):
            await api.hosted_page("")


class TestStripeCheckoutUrl:
    async def test_checkout_url_minimal(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"url": "https://checkout"})
        await api.stripe_checkout_url("https://success", "https://cancel")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/subscription/create-checkout",
            json={"success_url": "https://success", "cancel_url": "https://cancel"},
        )

    async def test_checkout_url_add_payment_method_only(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"url": "https://checkout"})
        await api.stripe_checkout_url(
            "https://success", "https://cancel", add_payment_method_only=True
        )
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["add_payment_method_only"] is True

    async def test_checkout_url_empty_success_url_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="success_url"):
            await api.stripe_checkout_url("", "https://cancel")

    async def test_checkout_url_empty_cancel_url_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="cancel_url"):
            await api.stripe_checkout_url("https://success", "")


class TestStripePortalUrl:
    async def test_portal_url_no_return_url(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"url": "https://portal"})
        await api.stripe_portal_url()
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/subscription/customer-portal",
            json={},
        )

    async def test_portal_url_with_return_url(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"url": "https://portal"})
        await api.stripe_portal_url(return_url="https://example.com/return")
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json == {"return_url": "https://example.com/return"}


class TestStripeSubscriptionLifecycle:
    async def test_stripe_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "active"})
        result = await api.stripe_get()
        mock_client._request_json.assert_called_once_with("GET", "/workspaces/2/subscription")
        assert result == {"status": "active"}

    async def test_stripe_create_minimal(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": "sub_1"})
        await api.stripe_create(42)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/subscription",
            json={"plan_id": 42},
        )

    async def test_stripe_create_with_billing_interval(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": "sub_1"})
        await api.stripe_create(42, billing_interval="yearly")
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json == {"plan_id": 42, "billing_interval": "yearly"}

    async def test_stripe_create_non_positive_plan_id_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="plan_id"):
            await api.stripe_create(0)

    async def test_stripe_cancel_no_body(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "cancelled"})
        await api.stripe_cancel()
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/subscription/cancel",
            json=None,
        )

    async def test_stripe_cancel_with_body(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "cancelled"})
        await api.stripe_cancel(body={"reason": "too expensive"})
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/subscription/cancel",
            json={"reason": "too expensive"},
        )

    async def test_stripe_end_trial(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "active"})
        await api.stripe_end_trial()
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/subscription/end-trial"
        )

    async def test_stripe_retry_payment(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "ok"})
        await api.stripe_retry_payment()
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/2/subscription/retry-payment"
        )

    async def test_stripe_sync(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "synced"})
        await api.stripe_sync()
        mock_client._request_json.assert_called_once_with("POST", "/workspaces/2/subscription/sync")

    async def test_stripe_status(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "active"})
        await api.stripe_status()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/subscription/status"
        )

    async def test_stripe_history(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"history": []})
        await api.stripe_history()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/subscription/billing-history"
        )

    async def test_stripe_usage(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"storage_gb": 5})
        await api.stripe_usage()
        mock_client._request_json.assert_called_once_with("GET", "/workspaces/2/subscription/usage")

    async def test_stripe_upcoming_invoice(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"amount_due": 100})
        await api.stripe_upcoming_invoice()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/subscription/upcoming-invoice"
        )


class TestStripePreviewInvoice:
    async def test_preview_invoice_no_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"amount_due": 0})
        await api.stripe_preview_invoice()
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/subscription/preview-invoice",
            params=None,
        )

    async def test_preview_invoice_with_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"amount_due": 500})
        await api.stripe_preview_invoice(
            connector_ids="ga_lib,facebook_ads",
            additional_storage_gb=10,
            additional_user_seats=2,
        )
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/subscription/preview-invoice",
            params={
                "connector_ids": "ga_lib,facebook_ads",
                "additional_storage_gb": 10,
                "additional_user_seats": 2,
            },
        )


class TestStripePaymentMethods:
    async def test_payment_method_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"payment_methods": []})
        await api.stripe_payment_method_list()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/subscription/payment-methods"
        )

    async def test_payment_method_set_default(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": "pm_123"})
        await api.stripe_payment_method_set_default("pm_123")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/subscription/payment-methods/default",
            json={"payment_method_id": "pm_123"},
        )

    async def test_payment_method_set_default_empty_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="payment_method_id"):
            await api.stripe_payment_method_set_default("")

    async def test_payment_method_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.stripe_payment_method_delete("pm_123")
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            "/workspaces/2/subscription/payment-methods/pm_123",
        )

    async def test_payment_method_delete_empty_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="payment_method_id"):
            await api.stripe_payment_method_delete("")


class TestInvoices:
    async def test_invoice_list_uses_stripe_billing_history(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"billing_history": []})
        assert await api.invoice_list() == {"billing_history": []}
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/2/subscription/billing-history"
        )

    def test_invoice_get_removed(self):
        api, _ = _make_api()
        assert not hasattr(api, "invoice_get")

    async def test_invoice_charge(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"status": "charged"})
        await api.invoice_charge()
        mock_client._request_json.assert_called_once_with("POST", "/workspaces/2/invoices/charge")


class TestSubscriptionDetail:
    async def test_subscription_get_no_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.subscription_get()
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/subscription_v1",
            params=None,
        )

    async def test_subscription_get_with_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1, "name": "Pro"})
        await api.subscription_get(fields="id,name")
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/subscription_v1",
            params={"fields": "id,name"},
        )

    async def test_subscription_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        patch = [{"op": "add", "path": "addons", "value": {"type": "storage", "count": 1}}]
        await api.subscription_update(patch)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/subscription_v1",
            json={"patch": patch},
        )

    async def test_subscription_update_empty_patch_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="patch"):
            await api.subscription_update([])
