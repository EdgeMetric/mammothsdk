"""Unit tests for the ``billing`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import billing as billing_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CHARGEBEE_PLAN = "mammoth.api.billing.BillingAPI.chargebee_plan"
_HOSTED_PAGE = "mammoth.api.billing.BillingAPI.hosted_page"
_INVOICE_CHARGE = "mammoth.api.billing.BillingAPI.invoice_charge"
_INVOICE_GET = "mammoth.api.billing.BillingAPI.invoice_get"
_INVOICE_LIST = "mammoth.api.billing.BillingAPI.invoice_list"
_STRIPE_CANCEL = "mammoth.api.billing.BillingAPI.stripe_cancel"
_STRIPE_CHECKOUT_URL = "mammoth.api.billing.BillingAPI.stripe_checkout_url"
_STRIPE_CREATE = "mammoth.api.billing.BillingAPI.stripe_create"
_STRIPE_END_TRIAL = "mammoth.api.billing.BillingAPI.stripe_end_trial"
_STRIPE_GET = "mammoth.api.billing.BillingAPI.stripe_get"
_STRIPE_HISTORY = "mammoth.api.billing.BillingAPI.stripe_history"
_STRIPE_PM_DELETE = "mammoth.api.billing.BillingAPI.stripe_payment_method_delete"
_STRIPE_PM_LIST = "mammoth.api.billing.BillingAPI.stripe_payment_method_list"
_STRIPE_PM_SET_DEFAULT = "mammoth.api.billing.BillingAPI.stripe_payment_method_set_default"
_STRIPE_PORTAL_URL = "mammoth.api.billing.BillingAPI.stripe_portal_url"
_STRIPE_PREVIEW_INVOICE = "mammoth.api.billing.BillingAPI.stripe_preview_invoice"
_STRIPE_RETRY_PAYMENT = "mammoth.api.billing.BillingAPI.stripe_retry_payment"
_STRIPE_STATUS = "mammoth.api.billing.BillingAPI.stripe_status"
_STRIPE_SYNC = "mammoth.api.billing.BillingAPI.stripe_sync"
_STRIPE_UPCOMING_INVOICE = "mammoth.api.billing.BillingAPI.stripe_upcoming_invoice"
_STRIPE_USAGE = "mammoth.api.billing.BillingAPI.stripe_usage"
_SUBSCRIPTION_GET = "mammoth.api.billing.BillingAPI.subscription_get"
_SUBSCRIPTION_UPDATE = "mammoth.api.billing.BillingAPI.subscription_update"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# --- chargebee-plan ---------------------------------------------------------------


def test_chargebee_plan_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_chargebee_plan(_inv("billing.chargebee-plan", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_chargebee_plan_requires_confirm_target(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_chargebee_plan(_inv("billing.chargebee-plan", yes=True, confirm="999"))
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_chargebee_plan_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_chargebee_plan(_inv("billing.chargebee-plan", yes=True, confirm="4"))
    assert fake_service.call_log == [(_CHARGEBEE_PLAN, {})]


# --- hosted-page -------------------------------------------------------------------


def test_hosted_page_requires_object_type(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_hosted_page(_inv("billing.hosted-page", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_hosted_page_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_hosted_page(
            _inv("billing.hosted-page", extra_args=["checkout_new"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_hosted_page_uses_positional_and_forwards_plan_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"plan_id": "plan_1"})
    billing_cmd.billing_hosted_page(
        _inv(
            "billing.hosted-page",
            extra_args=["checkout_new"],
            input_file=doc,
            yes=True,
            confirm="4",
        )
    )
    assert fake_service.call_log == [
        (_HOSTED_PAGE, {"object_type": "checkout_new", "plan_id": "plan_1"})
    ]


def test_hosted_page_object_type_from_input(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"object_type": "add_card"})
    billing_cmd.billing_hosted_page(
        _inv("billing.hosted-page", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_HOSTED_PAGE, {"object_type": "add_card"})]


# --- invoice.charge -----------------------------------------------------------------


def test_invoice_charge_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_invoice_charge(_inv("billing.invoice.charge", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_invoice_charge_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_invoice_charge(_inv("billing.invoice.charge", yes=True, confirm="4"))
    assert fake_service.call_log == [(_INVOICE_CHARGE, {})]


# --- invoice.get ---------------------------------------------------------------------


def test_invoice_get_requires_invoice_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_invoice_get(_inv("billing.invoice.get", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_invoice_get_invalid_invoice_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_invoice_get(
            _inv("billing.invoice.get", extra_args=["abc"], yes=True, confirm="abc")
        )
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


def test_invoice_get_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_invoice_get(
            _inv("billing.invoice.get", extra_args=["501"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_invoice_get_requires_confirm_equal_to_invoice_id(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_invoice_get(
            _inv("billing.invoice.get", extra_args=["501"], yes=True, confirm="4")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_invoice_get_proceeds_with_matching_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_invoice_get(
        _inv("billing.invoice.get", extra_args=["501"], yes=True, confirm="501")
    )
    assert fake_service.call_log == [(_INVOICE_GET, {"invoice_id": 501})]


# --- invoice.list --------------------------------------------------------------------


def test_invoice_list_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_invoice_list(_inv("billing.invoice.list", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_invoice_list_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"limit": 10, "sort": "-date"})
    billing_cmd.billing_invoice_list(
        _inv("billing.invoice.list", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_INVOICE_LIST, {"limit": 10, "sort": "-date"})]


# --- stripe.cancel -------------------------------------------------------------------


def test_stripe_cancel_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_cancel(_inv("billing.stripe.cancel", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_stripe_cancel_forwards_body(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"body": {"reason": "too expensive"}})
    billing_cmd.billing_stripe_cancel(
        _inv("billing.stripe.cancel", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_STRIPE_CANCEL, {"body": {"reason": "too expensive"}})]


# --- stripe.checkout-url --------------------------------------------------------------


def test_checkout_url_requires_success_url(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_checkout_url(
            _inv("billing.stripe.checkout-url", yes=True, confirm="4")
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_checkout_url_requires_cancel_url(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"success_url": "https://x/ok"})
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_checkout_url(
            _inv("billing.stripe.checkout-url", input_file=doc, yes=True, confirm="4")
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_checkout_url_blocked_without_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"success_url": "https://x/ok", "cancel_url": "https://x/cancel"})
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_checkout_url(
            _inv("billing.stripe.checkout-url", input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_checkout_url_forwards_optional_flag(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "success_url": "https://x/ok",
            "cancel_url": "https://x/cancel",
            "add_payment_method_only": True,
        },
    )
    billing_cmd.billing_stripe_checkout_url(
        _inv("billing.stripe.checkout-url", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [
        (
            _STRIPE_CHECKOUT_URL,
            {
                "success_url": "https://x/ok",
                "cancel_url": "https://x/cancel",
                "add_payment_method_only": True,
            },
        )
    ]


# --- stripe.create ---------------------------------------------------------------------


def test_stripe_create_requires_plan_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_create(_inv("billing.stripe.create", yes=True, confirm="4"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_stripe_create_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_create(
            _inv("billing.stripe.create", extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_stripe_create_forwards_billing_interval(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"billing_interval": "annual"})
    billing_cmd.billing_stripe_create(
        _inv("billing.stripe.create", extra_args=["9"], input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_STRIPE_CREATE, {"plan_id": 9, "billing_interval": "annual"})]


# --- stripe.end-trial --------------------------------------------------------------------


def test_stripe_end_trial_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_end_trial(_inv("billing.stripe.end-trial", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_stripe_end_trial_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_end_trial(_inv("billing.stripe.end-trial", yes=True, confirm="4"))
    assert fake_service.call_log == [(_STRIPE_END_TRIAL, {})]


# --- stripe.get ------------------------------------------------------------------------


def test_stripe_get_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_get(_inv("billing.stripe.get", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_stripe_get_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_get(_inv("billing.stripe.get", yes=True, confirm="4"))
    assert fake_service.call_log == [(_STRIPE_GET, {})]


# --- stripe.history --------------------------------------------------------------------


def test_stripe_history_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_history(_inv("billing.stripe.history", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_stripe_history_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_history(_inv("billing.stripe.history", yes=True, confirm="4"))
    assert fake_service.call_log == [(_STRIPE_HISTORY, {})]


# --- stripe.payment-method.delete -------------------------------------------------------


def test_pm_delete_requires_payment_method_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_payment_method_delete(
            _inv("billing.stripe.payment-method.delete", yes=True, confirm="pm_1")
        )
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_pm_delete_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_payment_method_delete(
            _inv(
                "billing.stripe.payment-method.delete",
                extra_args=["pm_1"],
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_pm_delete_requires_confirm_equal_to_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_payment_method_delete(
            _inv(
                "billing.stripe.payment-method.delete",
                extra_args=["pm_1"],
                yes=True,
                confirm="pm_other",
            )
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_pm_delete_proceeds_with_matching_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_payment_method_delete(
        _inv(
            "billing.stripe.payment-method.delete",
            extra_args=["pm_1"],
            yes=True,
            confirm="pm_1",
        )
    )
    assert fake_service.call_log == [(_STRIPE_PM_DELETE, {"payment_method_id": "pm_1"})]


# --- stripe.payment-method.list ----------------------------------------------------------


def test_pm_list_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_payment_method_list(
            _inv("billing.stripe.payment-method.list", output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_pm_list_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_payment_method_list(
        _inv("billing.stripe.payment-method.list", yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_STRIPE_PM_LIST, {})]


# --- stripe.payment-method.set-default ----------------------------------------------------


def test_pm_set_default_requires_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_payment_method_set_default(
            _inv("billing.stripe.payment-method.set-default", yes=True, confirm="pm_1")
        )
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_pm_set_default_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_payment_method_set_default(
            _inv(
                "billing.stripe.payment-method.set-default",
                extra_args=["pm_1"],
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_pm_set_default_proceeds_with_matching_confirm(
    fake_service: FakeMammothService,
) -> None:
    billing_cmd.billing_stripe_payment_method_set_default(
        _inv(
            "billing.stripe.payment-method.set-default",
            extra_args=["pm_1"],
            yes=True,
            confirm="pm_1",
        )
    )
    assert fake_service.call_log == [(_STRIPE_PM_SET_DEFAULT, {"payment_method_id": "pm_1"})]


# --- stripe.portal-url -------------------------------------------------------------------


def test_portal_url_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_portal_url(_inv("billing.stripe.portal-url", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_portal_url_forwards_return_url(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"return_url": "https://x/settings"})
    billing_cmd.billing_stripe_portal_url(
        _inv("billing.stripe.portal-url", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_STRIPE_PORTAL_URL, {"return_url": "https://x/settings"})]


# --- stripe.preview-invoice ----------------------------------------------------------------


def test_preview_invoice_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_preview_invoice(
            _inv("billing.stripe.preview-invoice", output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_preview_invoice_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "connector_ids": "conn_1,conn_2",
            "additional_storage_gb": 5,
            "additional_user_seats": 2,
        },
    )
    billing_cmd.billing_stripe_preview_invoice(
        _inv("billing.stripe.preview-invoice", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [
        (
            _STRIPE_PREVIEW_INVOICE,
            {
                "connector_ids": "conn_1,conn_2",
                "additional_storage_gb": 5,
                "additional_user_seats": 2,
            },
        )
    ]


# --- stripe.retry-payment ------------------------------------------------------------------


def test_retry_payment_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_retry_payment(
            _inv("billing.stripe.retry-payment", output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_retry_payment_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_retry_payment(
        _inv("billing.stripe.retry-payment", yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_STRIPE_RETRY_PAYMENT, {})]


# --- stripe.status --------------------------------------------------------------------------


def test_stripe_status_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_status(_inv("billing.stripe.status", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_stripe_status_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_status(_inv("billing.stripe.status", yes=True, confirm="4"))
    assert fake_service.call_log == [(_STRIPE_STATUS, {})]


# --- stripe.sync ----------------------------------------------------------------------------


def test_stripe_sync_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_sync(_inv("billing.stripe.sync", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_stripe_sync_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_sync(_inv("billing.stripe.sync", yes=True, confirm="4"))
    assert fake_service.call_log == [(_STRIPE_SYNC, {})]


# --- stripe.upcoming-invoice ------------------------------------------------------------------


def test_upcoming_invoice_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_upcoming_invoice(
            _inv("billing.stripe.upcoming-invoice", output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_upcoming_invoice_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_upcoming_invoice(
        _inv("billing.stripe.upcoming-invoice", yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_STRIPE_UPCOMING_INVOICE, {})]


# --- stripe.usage -------------------------------------------------------------------------------


def test_stripe_usage_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_usage(_inv("billing.stripe.usage", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_stripe_usage_proceeds_with_confirm(fake_service: FakeMammothService) -> None:
    billing_cmd.billing_stripe_usage(_inv("billing.stripe.usage", yes=True, confirm="4"))
    assert fake_service.call_log == [(_STRIPE_USAGE, {})]


# --- subscription.get --------------------------------------------------------------------------


def test_subscription_get_blocked_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_subscription_get(_inv("billing.subscription.get", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_subscription_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"fields": "plan,status"})
    billing_cmd.billing_subscription_get(
        _inv("billing.subscription.get", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_SUBSCRIPTION_GET, {"fields": "plan,status"})]


# --- subscription.update -----------------------------------------------------------------------


def test_subscription_update_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_subscription_update(
            _inv("billing.subscription.update", yes=True, confirm="4")
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_subscription_update_blocked_without_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"patch": [{"op": "replace", "path": "/seats", "value": 5}]})
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_subscription_update(
            _inv("billing.subscription.update", input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_subscription_update_proceeds_with_confirm(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"patch": [{"op": "replace", "path": "/seats", "value": 5}]})
    billing_cmd.billing_subscription_update(
        _inv("billing.subscription.update", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [
        (_SUBSCRIPTION_UPDATE, {"patch": [{"op": "replace", "path": "/seats", "value": 5}]})
    ]
