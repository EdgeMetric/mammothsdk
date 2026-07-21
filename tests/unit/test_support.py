"""Unit tests for the SupportAPI client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.support import SupportAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[SupportAPI, MagicMock]:
    """Create a SupportAPI with a mocked client."""
    mock_client = MagicMock()
    api = SupportAPI(mock_client)
    return api, mock_client


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------


class TestPlans:
    def test_plan_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"plans": []}
        result = api.plan_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/plans")
        assert result == {"plans": []}

    def test_plan_self_serve_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"plans": []}
        api.plan_self_serve_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/self-serve-plans")

    def test_plan_chargebee_list_default(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"available_plans": []}
        api.plan_chargebee_list()
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/sms", params={"resource": "plans"}
        )

    def test_plan_chargebee_list_custom_resource(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.plan_chargebee_list(resource="addons")
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/sms", params={"resource": "addons"}
        )

    def test_plan_get(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"plan": {"id": 5}}
        api.plan_get(5)
        mock_client._request_json.assert_called_once_with("GET", "/subscription/plans/5")

    def test_plan_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="plan_id"):
            api.plan_get(0)

    def test_plan_create_required_only(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"plan": {"id": 1}}
        api.plan_create("Pro", 49.0, True)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/plans",
            json={
                "name": "Pro",
                "monthly_price": 49.0,
                "is_self_serve": True,
                "annual_only": False,
                "storage_amount": 0,
                "number_of_tiers": 1,
            },
        )

    def test_plan_create_full(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"plan": {"id": 1}}
        api.plan_create(
            "Pro",
            49.0,
            True,
            display_name="Professional",
            description="desc",
            annual_price=499.0,
            annual_only=True,
            trial_days=14,
            storage_amount=100,
            max_storage=1000,
            max_users=25,
            no_of_users=5,
            seat_price=9.99,
            number_of_tiers=2,
            storage_block_size=10,
            tiers=[{"gb": 500, "price_per_gb": 0.1}],
            connector_profile_id=1,
            feature_profile_id=2,
        )
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["display_name"] == "Professional"
        assert call_json["description"] == "desc"
        assert call_json["annual_price"] == 499.0
        assert call_json["tiers"] == [{"gb": 500, "price_per_gb": 0.1}]
        assert call_json["connector_profile_id"] == 1
        assert call_json["feature_profile_id"] == 2

    def test_plan_update_partial(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.plan_update(5, name="New Name")
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/plans/5", json={"name": "New Name"}
        )

    def test_plan_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="plan_id"):
            api.plan_update(-1, name="x")

    def test_plan_update_storage_tiers(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        tiers = [{"gb": 100, "price_per_gb": 0.5}]
        api.plan_update_storage_tiers(5, tiers)
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/plans/5/storage-tiers", json={"storage_tiers": tiers}
        )

    def test_plan_update_storage_tiers_empty(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="storage_tiers"):
            api.plan_update_storage_tiers(5, [])

    def test_plan_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.plan_delete(5)
        mock_client._request_json.assert_called_once_with("DELETE", "/subscription/plans/5")

    def test_plan_archive(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.plan_archive(5)
        mock_client._request_json.assert_called_once_with("POST", "/subscription/plans/5/archive")


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------


class TestFeatures:
    def test_feature_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"features": []}
        api.feature_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/features")

    def test_feature_create_defaults(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.feature_create("API Rate Limit")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/features",
            json={"name": "API Rate Limit", "price_per_month": 0, "enabled": True},
        )

    def test_feature_create_with_values(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.feature_create("API Rate Limit", description="desc", values=["1000/hour", "5000/hour"])
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["description"] == "desc"
        assert call_json["values"] == ["1000/hour", "5000/hour"]

    def test_feature_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.feature_update(3, enabled=False)
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/features/3", json={"enabled": False}
        )

    def test_feature_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="feature_id"):
            api.feature_update(0)

    def test_feature_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.feature_delete(3)
        mock_client._request_json.assert_called_once_with("DELETE", "/subscription/features/3")


# ---------------------------------------------------------------------------
# Feature profiles
# ---------------------------------------------------------------------------


class TestFeatureProfiles:
    def test_feature_profile_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"feature_profiles": []}
        api.feature_profile_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/feature-profiles")

    def test_feature_profile_create(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.feature_profile_create("Standard")
        mock_client._request_json.assert_called_once_with(
            "POST", "/subscription/feature-profiles", json={"name": "Standard"}
        )

    def test_feature_profile_create_with_features(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        features = [{"feature_id": 1, "price_per_month": 5, "enabled": True}]
        api.feature_profile_create("Standard", description="desc", features=features)
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["features"] == features

    def test_feature_profile_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.feature_profile_update(7, name="Renamed")
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/feature-profiles/7", json={"name": "Renamed"}
        )

    def test_feature_profile_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="profile_id"):
            api.feature_profile_update(0)

    def test_feature_profile_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.feature_profile_delete(7)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/subscription/feature-profiles/7"
        )

    def test_feature_profile_add_feature(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.feature_profile_add_feature(7, 3, value="5000/hour")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/feature-profiles/7/features",
            json={
                "feature_id": 3,
                "price_per_month": 0,
                "enabled": True,
                "value": "5000/hour",
            },
        )

    def test_feature_profile_add_feature_invalid_profile_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="profile_id"):
            api.feature_profile_add_feature(0, 3)


# ---------------------------------------------------------------------------
# Connectors
# ---------------------------------------------------------------------------


class TestConnectors:
    def test_connector_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"connectors": []}
        api.connector_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/connectors")

    def test_connector_create_defaults(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.connector_create("Salesforce")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/connectors",
            json={"name": "Salesforce", "price_per_month": 0, "enabled": True},
        )

    def test_connector_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.connector_update(4, price_per_month=15.0)
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/connectors/4", json={"price_per_month": 15.0}
        )

    def test_connector_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="connector_id"):
            api.connector_update(0)

    def test_connector_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.connector_delete(4)
        mock_client._request_json.assert_called_once_with("DELETE", "/subscription/connectors/4")


# ---------------------------------------------------------------------------
# Connector profiles
# ---------------------------------------------------------------------------


class TestConnectorProfiles:
    def test_connector_profile_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"connector_profiles": []}
        api.connector_profile_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/connector-profiles")

    def test_connector_profile_create(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.connector_profile_create("Enterprise")
        mock_client._request_json.assert_called_once_with(
            "POST", "/subscription/connector-profiles", json={"name": "Enterprise"}
        )

    def test_connector_profile_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.connector_profile_update(9, description="new desc")
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/connector-profiles/9", json={"description": "new desc"}
        )

    def test_connector_profile_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="profile_id"):
            api.connector_profile_update(0)

    def test_connector_profile_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.connector_profile_delete(9)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/subscription/connector-profiles/9"
        )

    def test_connector_profile_add_connector(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.connector_profile_add_connector(9, 2, price_per_month=10.0, enabled=False)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/connector-profiles/9/connectors",
            json={"connector_id": 2, "price_per_month": 10.0, "enabled": False},
        )

    def test_connector_profile_add_connector_invalid_profile_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="profile_id"):
            api.connector_profile_add_connector(0, 2)


# ---------------------------------------------------------------------------
# Workspace subscriptions
# ---------------------------------------------------------------------------


class TestSubscriptions:
    def test_subscription_get(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.subscription_get(4)
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4/sms", params=None
        )

    def test_subscription_get_with_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.subscription_get(4, fields="plan_id,status")
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4/sms", params={"fields": "plan_id,status"}
        )

    def test_subscription_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            api.subscription_get(0)

    def test_subscription_create_with_customer_id(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.subscription_create(4, "plan_1", customer_id="cus_123")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/support/workspaces/4/sms",
            json={"plan_id": "plan_1", "customer_id": "cus_123"},
        )

    def test_subscription_create_with_new_customer(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.subscription_create(
            4,
            "plan_1",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company_name="Acme",
        )
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["first_name"] == "John"
        assert call_json["company_name"] == "Acme"

    def test_subscription_create_missing_customer_details(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="customer_id"):
            api.subscription_create(4, "plan_1", first_name="John")

    def test_subscription_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.subscription_update(4, "sub_new_123")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/support/workspaces/4/sms",
            json={"patch": [{"op": "replace", "path": "subscription_id", "value": "sub_new_123"}]},
        )


# ---------------------------------------------------------------------------
# Users (global) and ownership transfer
# ---------------------------------------------------------------------------


class TestUsers:
    def test_user_register(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"user_id": 1}
        api.user_register("john@example.com", "John", "Smith", False)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/support/users",
            json={
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Smith",
                "verified": False,
            },
        )

    def test_user_register_with_is_registration(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.user_register("john@example.com", "John", "Smith", False, is_registration=True)
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["is_registration"] is True

    def test_user_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.user_update("john@example.com", True)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/support/users",
            json={
                "patch": [
                    {
                        "op": "replace",
                        "path": "verified",
                        "value": {"email": "john@example.com", "verified": True},
                    }
                ]
            },
        )

    def test_user_list_all_no_params(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"users": []}
        api.user_list_all()
        mock_client._request_json.assert_called_once_with("GET", "/settings/users", params=None)

    def test_user_list_all_with_params(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"users": []}
        api.user_list_all(limit=10, offset=5, sort="(email:asc)", fields="email")
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/settings/users",
            params={"fields": "email", "sort": "(email:asc)", "offset": 5, "limit": 10},
        )

    def test_ownership_transfer(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.ownership_transfer(1, 29, remove_role="workspace_member")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/settings/users",
            json={
                "patches": [
                    {
                        "op": "replace",
                        "path": "role",
                        "value": {
                            "workspace_id": 1,
                            "user_id": 29,
                            "new_role": "workspace_owner",
                            "remove_role": "workspace_member",
                        },
                    }
                ]
            },
        )

    def test_ownership_transfer_invalid_workspace_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            api.ownership_transfer(0, 29)


# ---------------------------------------------------------------------------
# Workspaces (support/admin)
# ---------------------------------------------------------------------------


class TestWorkspaces:
    def test_workspace_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"workspaces": []}
        api.workspace_list()
        mock_client._request_json.assert_called_once_with("GET", "/support/workspaces")

    def test_workspace_get(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_get(4)
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4", params=None
        )

    def test_workspace_get_with_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_get(4, fields="name,status")
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4", params={"fields": "name,status"}
        )

    def test_workspace_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            api.workspace_get(0)

    def test_workspace_create_required_only(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_create("Docs", "test@test.com", "monthly")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/support/workspaces",
            json={
                "name": "Docs",
                "user_email": "test@test.com",
                "payment_frequency": "monthly",
                "is_verified": True,
                "is_registration": False,
            },
        )

    def test_workspace_create_full(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_create(
            "Docs",
            "test@test.com",
            "yearly",
            plan_id=1,
            origin="WEBSITE_PLAN_SELECTION",
            is_verified=False,
            is_registration=True,
            file_id="file_123",
            table_number=1,
            plan_create={"name": "Inline Plan"},
        )
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["plan_id"] == 1
        assert call_json["origin"] == "WEBSITE_PLAN_SELECTION"
        assert call_json["file_id"] == "file_123"
        assert call_json["plan_create"] == {"name": "Inline Plan"}

    def test_workspace_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_update(4, "Docs", "monthly", 2)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/support/workspaces/4",
            json={"name": "Docs", "payment_frequency": "monthly", "plan_id": 2},
        )

    def test_workspace_update_with_plan_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_update(4, "Docs", "monthly", 2, plan_update={"monthly_price": 59.0})
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["plan_update"] == {"monthly_price": 59.0}

    def test_workspace_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            api.workspace_update(0, "Docs", "monthly", 2)

    def test_workspace_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_delete(4)
        mock_client._request_json.assert_called_once_with("DELETE", "/support/workspaces/4")

    def test_workspace_suspend_access(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_suspend_access(4, reason="Non-payment")
        mock_client._request_json.assert_called_once_with(
            "POST", "/support/workspaces/4/suspend-access", json={"reason": "Non-payment"}
        )

    def test_workspace_suspend_access_no_reason(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_suspend_access(4)
        mock_client._request_json.assert_called_once_with(
            "POST", "/support/workspaces/4/suspend-access", json={}
        )

    def test_workspace_restore_access(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_restore_access(4)
        mock_client._request_json.assert_called_once_with(
            "POST", "/support/workspaces/4/restore-access"
        )


# ---------------------------------------------------------------------------
# Workspace users (support/admin)
# ---------------------------------------------------------------------------


class TestWorkspaceUsers:
    def test_workspace_user_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"users": []}
        api.workspace_user_list(4)
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4/users", params=None
        )

    def test_workspace_user_list_with_params(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"users": []}
        api.workspace_user_list(4, limit=10, offset=0, fields="email", sort="(email:asc)")
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/support/workspaces/4/users",
            params={"limit": 10, "offset": 0, "fields": "email", "sort": "(email:asc)"},
        )

    def test_workspace_user_list_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            api.workspace_user_list(0)

    def test_workspace_user_add(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1}
        api.workspace_user_add(4, "jane@example.com", "workspace_admin", first_name="Jane")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/support/workspaces/4/users",
            json={"email": "jane@example.com", "role": "workspace_admin", "first_name": "Jane"},
        )

    def test_workspace_user_add_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            api.workspace_user_add(0, "jane@example.com", "workspace_admin")

    def test_workspace_user_remove(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_user_remove(4, 9)
        mock_client._request_json.assert_called_once_with("DELETE", "/support/workspaces/4/users/9")

    def test_workspace_user_remove_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            api.workspace_user_remove(0, 9)

    def test_workspace_user_transfer(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_user_transfer(4, 29, "workspace_admin", remove_role="workspace_owner")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/support/workspaces/4/users",
            json={
                "patch": [
                    {
                        "op": "replace",
                        "path": "role",
                        "value": {
                            "user_id": 29,
                            "role": "workspace_admin",
                            "remove_role": "workspace_owner",
                        },
                    }
                ]
            },
        )

    def test_workspace_user_transfer_no_remove_role(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.workspace_user_transfer(4, 29, "workspace_admin")
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["patch"][0]["value"]["remove_role"] is None

    def test_workspace_user_transfer_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            api.workspace_user_transfer(0, 29, "workspace_admin")
