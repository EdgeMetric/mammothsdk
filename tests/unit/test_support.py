"""Unit tests for the SupportAPI client."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock

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
    async def test_plan_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"plans": []})
        result = await api.plan_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/plans")
        assert result == {"plans": []}

    async def test_plan_self_serve_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"plans": []})
        await api.plan_self_serve_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/self-serve-plans")

    async def test_plan_chargebee_list_default(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"available_plans": []})
        await api.plan_chargebee_list()
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/sms", params={"resource": "plans"}
        )

    async def test_plan_chargebee_list_custom_resource(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.plan_chargebee_list(resource="addons")
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/sms", params={"resource": "addons"}
        )

    async def test_plan_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"plan": {"id": 5}})
        await api.plan_get(5)
        mock_client._request_json.assert_called_once_with("GET", "/subscription/plans/5")

    async def test_plan_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="plan_id"):
            await api.plan_get(0)

    async def test_plan_create_required_only(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"plan": {"id": 1}})
        await api.plan_create("Pro", 49.0, True)
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

    async def test_plan_create_full(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"plan": {"id": 1}})
        await api.plan_create(
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

    async def test_plan_update_partial(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.plan_update(5, name="New Name")
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/plans/5", json={"name": "New Name"}
        )

    async def test_plan_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="plan_id"):
            await api.plan_update(-1, name="x")

    async def test_plan_update_storage_tiers(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        tiers = [{"gb": 100, "price_per_gb": 0.5}]
        await api.plan_update_storage_tiers(5, tiers)
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/plans/5/storage-tiers", json={"storage_tiers": tiers}
        )

    async def test_plan_update_storage_tiers_empty(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="storage_tiers"):
            await api.plan_update_storage_tiers(5, [])

    async def test_plan_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.plan_delete(5)
        mock_client._request_json.assert_called_once_with("DELETE", "/subscription/plans/5")

    async def test_plan_archive(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.plan_archive(5)
        mock_client._request_json.assert_called_once_with("POST", "/subscription/plans/5/archive")


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------


class TestFeatures:
    async def test_feature_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"features": []})
        await api.feature_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/features")

    async def test_feature_create_defaults(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.feature_create("API Rate Limit")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/features",
            json={"name": "API Rate Limit", "price_per_month": 0, "enabled": True},
        )

    async def test_feature_create_with_values(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.feature_create(
            "API Rate Limit", description="desc", values=["1000/hour", "5000/hour"]
        )
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["description"] == "desc"
        assert call_json["values"] == ["1000/hour", "5000/hour"]

    async def test_feature_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.feature_update(3, enabled=False)
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/features/3", json={"enabled": False}
        )

    async def test_feature_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="feature_id"):
            await api.feature_update(0)

    async def test_feature_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.feature_delete(3)
        mock_client._request_json.assert_called_once_with("DELETE", "/subscription/features/3")


# ---------------------------------------------------------------------------
# Feature profiles
# ---------------------------------------------------------------------------


class TestFeatureProfiles:
    async def test_feature_profile_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"feature_profiles": []})
        await api.feature_profile_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/feature-profiles")

    async def test_feature_profile_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.feature_profile_create("Standard")
        mock_client._request_json.assert_called_once_with(
            "POST", "/subscription/feature-profiles", json={"name": "Standard"}
        )

    async def test_feature_profile_create_with_features(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        features = [{"feature_id": 1, "price_per_month": 5, "enabled": True}]
        await api.feature_profile_create("Standard", description="desc", features=features)
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["features"] == features

    async def test_feature_profile_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.feature_profile_update(7, name="Renamed")
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/feature-profiles/7", json={"name": "Renamed"}
        )

    async def test_feature_profile_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="profile_id"):
            await api.feature_profile_update(0)

    async def test_feature_profile_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.feature_profile_delete(7)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/subscription/feature-profiles/7"
        )

    async def test_feature_profile_add_feature(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.feature_profile_add_feature(7, 3, value="5000/hour")
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

    async def test_feature_profile_add_feature_invalid_profile_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="profile_id"):
            await api.feature_profile_add_feature(0, 3)


# ---------------------------------------------------------------------------
# Connectors
# ---------------------------------------------------------------------------


class TestConnectors:
    async def test_connector_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"connectors": []})
        await api.connector_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/connectors")

    async def test_connector_create_defaults(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.connector_create("Salesforce")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/connectors",
            json={"name": "Salesforce", "enabled": True},
        )

    async def test_connector_create_never_sends_the_removed_price(self):
        """Prod dropped ``price_per_month``: a caller's value warns and is not sent."""
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        with pytest.warns(DeprecationWarning, match="price_per_month"):
            await api.connector_create("Salesforce", price_per_month=9.5)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/connectors",
            json={"name": "Salesforce", "enabled": True},
        )

    async def test_connector_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.connector_update(4, name="Salesforce 2", enabled=False)
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/connectors/4", json={"name": "Salesforce 2", "enabled": False}
        )

    async def test_connector_update_never_sends_the_removed_price(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        with pytest.warns(DeprecationWarning, match="price_per_month"):
            await api.connector_update(4, name="X", price_per_month=15.0)
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/connectors/4", json={"name": "X"}
        )

    async def test_connector_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="connector_id"):
            await api.connector_update(0)

    async def test_connector_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.connector_delete(4)
        mock_client._request_json.assert_called_once_with("DELETE", "/subscription/connectors/4")


# ---------------------------------------------------------------------------
# Connector profiles
# ---------------------------------------------------------------------------


class TestConnectorProfiles:
    async def test_connector_profile_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"connector_profiles": []})
        await api.connector_profile_list()
        mock_client._request_json.assert_called_once_with("GET", "/subscription/connector-profiles")

    async def test_connector_profile_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.connector_profile_create("Enterprise")
        mock_client._request_json.assert_called_once_with(
            "POST", "/subscription/connector-profiles", json={"name": "Enterprise"}
        )

    async def test_connector_profile_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.connector_profile_update(9, description="new desc")
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/connector-profiles/9", json={"description": "new desc"}
        )

    async def test_connector_profile_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="profile_id"):
            await api.connector_profile_update(0)

    async def test_connector_profile_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.connector_profile_delete(9)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/subscription/connector-profiles/9"
        )

    async def test_connector_profile_add_connector(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.connector_profile_add_connector(9, 2, price_per_month=10.0, enabled=False)
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/connector-profiles/9/connectors",
            json={"connector_id": 2, "price_per_month": 10.0, "enabled": False},
        )

    async def test_connector_profile_add_connector_invalid_profile_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="profile_id"):
            await api.connector_profile_add_connector(0, 2)


# ---------------------------------------------------------------------------
# Workspace subscriptions
# ---------------------------------------------------------------------------


class TestSubscriptions:
    async def test_subscription_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.subscription_get(4)
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4/sms", params=None
        )

    async def test_subscription_get_with_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.subscription_get(4, fields="plan_id,status")
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4/sms", params={"fields": "plan_id,status"}
        )

    async def test_subscription_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.subscription_get(0)

    async def test_subscription_create_with_customer_id(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.subscription_create(4, "plan_1", customer_id="cus_123")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/support/workspaces/4/sms",
            json={"plan_id": "plan_1", "customer_id": "cus_123"},
        )

    async def test_subscription_create_with_new_customer(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.subscription_create(
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

    async def test_subscription_create_missing_customer_details(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="customer_id"):
            await api.subscription_create(4, "plan_1", first_name="John")

    async def test_subscription_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.subscription_update(4, "sub_new_123")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/support/workspaces/4/sms",
            json={"patch": [{"op": "replace", "path": "subscription_id", "value": "sub_new_123"}]},
        )


# ---------------------------------------------------------------------------
# Users (global) and ownership transfer
# ---------------------------------------------------------------------------


class TestUsers:
    async def test_user_register(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"user_id": 1})
        await api.user_register("john@example.com", "John", "Smith", False)
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

    async def test_user_register_with_is_registration(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.user_register("john@example.com", "John", "Smith", False, is_registration=True)
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["is_registration"] is True

    async def test_user_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.user_update("john@example.com", True)
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

    async def test_user_list_all_no_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"users": []})
        await api.user_list_all()
        mock_client._request_json.assert_called_once_with("GET", "/settings/users", params=None)

    async def test_user_list_all_with_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"users": []})
        await api.user_list_all(limit=10, offset=5, sort="(email:asc)", fields="email")
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/settings/users",
            params={"fields": "email", "sort": "(email:asc)", "offset": 5, "limit": 10},
        )

    async def test_ownership_transfer(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.ownership_transfer(1, 29, remove_role="workspace_member")
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

    async def test_ownership_transfer_invalid_workspace_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.ownership_transfer(0, 29)


# ---------------------------------------------------------------------------
# Workspaces (support/admin)
# ---------------------------------------------------------------------------


class TestWorkspaces:
    async def test_workspace_list(self):
        api, mock_client = _make_api()
        mock_client._request = AsyncMock(return_value={"workspaces": []})
        result = await api.workspace_list()
        mock_client._request.assert_called_once_with(
            "GET",
            "/support/workspaces",
            params={"limit": 100, "offset": 0},
            expected_response_shape="list_or_dict",
        )
        assert result == {"workspaces": []}

    async def test_workspace_list_wraps_bare_array(self):
        # The release backend answers this route with a bare JSON array.
        api, mock_client = _make_api()
        mock_client._request = AsyncMock(return_value=[{"id": 4}, {"id": 5}])
        assert await api.workspace_list() == {"workspaces": [{"id": 4}, {"id": 5}]}

    async def test_workspace_list_follows_pages_past_the_default_of_fifty(self):
        """Prod pages this route; one unparameterised call would stop at 50 workspaces."""
        api, mock_client = _make_api()
        first = [{"id": i} for i in range(1, 101)]
        second = [{"id": i} for i in range(101, 131)]
        mock_client._request = AsyncMock(
            side_effect=[{"workspaces": first, "limit": 100}, {"workspaces": second, "limit": 100}]
        )
        result = await api.workspace_list()
        assert [w["id"] for w in result["workspaces"]] == list(range(1, 131))
        offsets = [c.kwargs["params"]["offset"] for c in mock_client._request.call_args_list]
        assert offsets == [0, 100]

    async def test_workspace_list_stops_when_the_backend_ignores_paging(self):
        api, mock_client = _make_api()
        everything = [{"id": i} for i in range(1, 151)]
        mock_client._request = AsyncMock(return_value=everything)
        result = await api.workspace_list()
        assert result == {"workspaces": everything}
        assert mock_client._request.await_count == 2

    async def test_workspace_list_stops_on_a_repeated_page_of_rows_without_ids(self):
        api, mock_client = _make_api()
        everything = [{"name": f"w{i}"} for i in range(150)]
        mock_client._request = AsyncMock(return_value=everything)
        result = await api.workspace_list()
        assert result == {"workspaces": everything}
        assert mock_client._request.await_count == 2

    async def test_workspace_list_leaves_the_instance_types_variant_alone(self):
        api, mock_client = _make_api()
        body = {"instance_types": [{"name": "small"}]}
        mock_client._request = AsyncMock(return_value=body)
        assert await api.workspace_list() == body

    async def test_workspace_get(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_get(4)
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4", params=None
        )

    async def test_workspace_get_with_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_get(4, fields="name,status")
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4", params={"fields": "name,status"}
        )

    async def test_workspace_get_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.workspace_get(0)

    async def test_workspace_create_required_only(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_create("Docs", "test@test.com", "monthly")
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

    async def test_workspace_create_full(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_create(
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

    async def test_workspace_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_update(4, "Docs", "monthly", 2)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/support/workspaces/4",
            json={"name": "Docs", "payment_frequency": "monthly", "plan_id": 2},
        )

    async def test_workspace_update_with_plan_update(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_update(4, "Docs", "monthly", 2, plan_update={"monthly_price": 59.0})
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["plan_update"] == {"monthly_price": 59.0}

    async def test_workspace_update_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.workspace_update(0, "Docs", "monthly", 2)

    async def test_workspace_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_delete(4)
        mock_client._request_json.assert_called_once_with("DELETE", "/support/workspaces/4")

    async def test_workspace_suspend_access(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_suspend_access(4, reason="Non-payment")
        mock_client._request_json.assert_called_once_with(
            "POST", "/support/workspaces/4/suspend-access", json={"reason": "Non-payment"}
        )

    async def test_workspace_suspend_access_no_reason(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_suspend_access(4)
        mock_client._request_json.assert_called_once_with(
            "POST", "/support/workspaces/4/suspend-access", json={}
        )

    async def test_workspace_restore_access(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_restore_access(4)
        mock_client._request_json.assert_called_once_with(
            "POST", "/support/workspaces/4/restore-access"
        )


# ---------------------------------------------------------------------------
# Workspace users (support/admin)
# ---------------------------------------------------------------------------


class TestWorkspaceUsers:
    async def test_workspace_user_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"users": []})
        await api.workspace_user_list(4)
        mock_client._request_json.assert_called_once_with(
            "GET", "/support/workspaces/4/users", params=None
        )

    async def test_workspace_user_list_with_params(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"users": []})
        await api.workspace_user_list(4, limit=10, offset=0, fields="email", sort="(email:asc)")
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/support/workspaces/4/users",
            params={"limit": 10, "offset": 0, "fields": "email", "sort": "(email:asc)"},
        )

    async def test_workspace_user_list_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.workspace_user_list(0)

    async def test_workspace_user_add(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"id": 1})
        await api.workspace_user_add(4, "jane@example.com", "workspace_admin", first_name="Jane")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/support/workspaces/4/users",
            json={"email": "jane@example.com", "role": "workspace_admin", "first_name": "Jane"},
        )

    async def test_workspace_user_add_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.workspace_user_add(0, "jane@example.com", "workspace_admin")

    async def test_workspace_user_remove(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_user_remove(4, 9)
        mock_client._request_json.assert_called_once_with("DELETE", "/support/workspaces/4/users/9")

    async def test_workspace_user_remove_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.workspace_user_remove(0, 9)

    async def test_workspace_user_transfer(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_user_transfer(4, 29, "workspace_admin", remove_role="workspace_owner")
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

    async def test_workspace_user_transfer_no_remove_role(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.workspace_user_transfer(4, 29, "workspace_admin")
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["patch"][0]["value"]["remove_role"] is None

    async def test_workspace_user_transfer_invalid_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.workspace_user_transfer(0, 29, "workspace_admin")


# ---------------------------------------------------------------------------
# Plan unarchive and storage options
# ---------------------------------------------------------------------------


class TestPlanStorageOptions:
    async def test_plan_unarchive(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.plan_unarchive(5)
        mock_client._request_json.assert_called_once_with("POST", "/subscription/plans/5/unarchive")

    async def test_storage_option_list(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"storage_options": []})
        await api.plan_storage_option_list(5)
        mock_client._request_json.assert_called_once_with(
            "GET", "/subscription/plans/5/storage-options"
        )

    async def test_storage_option_create(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.plan_storage_option_create(
            5, storage_gb=100, monthly_price=20.0, annual_price=200
        )
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/subscription/plans/5/storage-options",
            json={"storage_gb": 100, "monthly_price": 20.0, "annual_price": 200},
        )

    async def test_storage_option_update_sends_only_given_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.plan_storage_option_update(5, 9, monthly_price=25.0)
        mock_client._request_json.assert_called_once_with(
            "PUT", "/subscription/plans/5/storage-options/9", json={"monthly_price": 25.0}
        )

    async def test_storage_option_update_without_fields_raises(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock()
        with pytest.raises(MammothValidationError, match="at least one"):
            await api.plan_storage_option_update(5, 9)
        mock_client._request_json.assert_not_called()

    async def test_storage_option_archive(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.plan_storage_option_archive(5, 9)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/subscription/plans/5/storage-options/9"
        )

    @pytest.mark.parametrize(
        "call",
        [
            lambda api: api.plan_unarchive(0),
            lambda api: api.plan_storage_option_list(-1),
            lambda api: api.plan_storage_option_archive(5, 0),
        ],
    )
    async def test_rejects_non_positive_ids(self, call):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock()
        with pytest.raises(MammothValidationError, match="positive integer"):
            await call(api)
        mock_client._request_json.assert_not_called()


# ---------------------------------------------------------------------------
# Curated template catalog (platform admin)
# ---------------------------------------------------------------------------

_ADMIN = "/dashboards/v3/templates/admin"


class TestTemplateAdmin:
    @pytest.mark.parametrize(
        ("call", "method", "path"),
        [
            (lambda api: api.template_list(), "GET", _ADMIN),
            (lambda api: api.template_data_preview("sales"), "GET", f"{_ADMIN}/sales/data-preview"),
            (lambda api: api.template_canvas("sales"), "GET", f"{_ADMIN}/sales/canvas"),
            (lambda api: api.template_publish("sales"), "POST", f"{_ADMIN}/sales/publish"),
            (lambda api: api.template_unpublish("sales"), "POST", f"{_ADMIN}/sales/unpublish"),
            (lambda api: api.template_retire("sales"), "POST", f"{_ADMIN}/sales/retire"),
            (
                lambda api: api.template_thumbnail_clear("sales"),
                "DELETE",
                f"{_ADMIN}/sales/thumbnail",
            ),
            (lambda api: api.template_discard("sales"), "DELETE", f"{_ADMIN}/sales"),
            (lambda api: api.template_snapshots(), "GET", f"{_ADMIN}/snapshots"),
            (lambda api: api.template_audit(), "GET", f"{_ADMIN}/audit"),
        ],
    )
    async def test_route(self, call, method, path):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await call(api)
        mock_client._request_json.assert_called_once_with(method, path)

    async def test_slug_is_path_encoded(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.template_publish("a/b")
        mock_client._request_json.assert_called_once_with("POST", f"{_ADMIN}/a%2Fb/publish")

    async def test_empty_slug_raises(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock()
        with pytest.raises(MammothValidationError, match="slug"):
            await api.template_retire("")
        mock_client._request_json.assert_not_called()

    async def test_edit_wraps_changes_in_params_and_keeps_nulls(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.template_edit("sales", {"title": "Sales", "function": None})
        mock_client._request_json.assert_called_once_with(
            "PATCH", f"{_ADMIN}/sales", json={"params": {"title": "Sales", "function": None}}
        )

    async def test_edit_without_changes_raises(self):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock()
        with pytest.raises(MammothValidationError, match="changes"):
            await api.template_edit("sales", {})
        mock_client._request_json.assert_not_called()

    async def test_inspect_uploads_the_bundle_as_data_part(self, tmp_path):
        bundle = tmp_path / "sales.zip"
        bundle.write_bytes(b"PK\x03\x04")
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={"slug": "sales"})
        await api.template_inspect(bundle)
        args, kwargs = mock_client._request_json.call_args
        assert args == ("POST", f"{_ADMIN}/inspect")
        [(part, (name, _stream, media_type))] = kwargs["files"]
        assert (part, name, media_type) == ("data", "sales.zip", "application/zip")

    async def test_import_binds_dataset(self, tmp_path):
        bundle = tmp_path / "sales.zip"
        bundle.write_bytes(b"PK\x03\x04")
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.template_import(bundle, dataset="Orders")
        args, kwargs = mock_client._request_json.call_args
        assert args == ("POST", f"{_ADMIN}/import")
        assert kwargs["params"] == {"dataset": "Orders"}

    async def test_import_without_dataset_sends_no_query(self, tmp_path):
        bundle = tmp_path / "sales.zip"
        bundle.write_bytes(b"PK\x03\x04")
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.template_import(bundle)
        assert mock_client._request_json.call_args.kwargs["params"] is None

    async def test_import_missing_file_raises(self, tmp_path):
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock()
        with pytest.raises(MammothValidationError, match="File not found"):
            await api.template_import(tmp_path / "absent.zip")
        mock_client._request_json.assert_not_called()

    async def test_thumbnail_set_uploads_the_image(self, tmp_path):
        image = tmp_path / "card.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n")
        api, mock_client = _make_api()
        mock_client._request_json = AsyncMock(return_value={})
        await api.template_thumbnail_set("sales", image)
        args, kwargs = mock_client._request_json.call_args
        assert args == ("PUT", f"{_ADMIN}/sales/thumbnail")
        assert kwargs["files"][0][0] == "data"

    async def test_export_writes_the_zip(self, tmp_path):
        api, mock_client = _make_api()
        mock_client._request_binary = AsyncMock(
            return_value={"content_base64": base64.b64encode(b"PK-zip").decode()}
        )
        out = await api.template_export("sales", output_path=tmp_path / "s.zip", with_data=True)
        mock_client._request_binary.assert_called_once_with(
            "GET", f"{_ADMIN}/sales/export", params={"data": "1"}
        )
        assert out.read_bytes() == b"PK-zip"

    async def test_export_dashboard_passes_slug_and_data_flag(self, tmp_path):
        api, mock_client = _make_api()
        mock_client._request_binary = AsyncMock(
            return_value={"content_base64": base64.b64encode(b"PK").decode()}
        )
        out = await api.template_export_dashboard(
            42, "my-board", output_path=tmp_path / "b.zip", with_data=False
        )
        mock_client._request_binary.assert_called_once_with(
            "GET", f"{_ADMIN}/dashboards/42/export", params={"slug": "my-board", "data": "0"}
        )
        assert out == tmp_path / "b.zip"

    async def test_export_dashboard_requires_slug(self):
        api, mock_client = _make_api()
        mock_client._request_binary = AsyncMock()
        with pytest.raises(MammothValidationError, match="slug"):
            await api.template_export_dashboard(42, "")
        mock_client._request_binary.assert_not_called()


# ---------------------------------------------------------------------------
# Billing actions
# ---------------------------------------------------------------------------


def _call_api(returns: object = None) -> tuple[SupportAPI, AsyncMock]:
    """A SupportAPI whose HTTP seam is an AsyncMock returning *returns*."""
    api, mock_client = _make_api()
    mock_client._request_json = AsyncMock(return_value=returns if returns is not None else {})
    return api, mock_client._request_json


class TestBillingActions:
    async def test_start_trial_default_length(self):
        api, call = _call_api({"message": "ok", "trial": {}})
        await api.billing_start_trial(12)
        call.assert_called_once_with("POST", "/support/billing/12/start-trial", json={})

    async def test_start_trial_with_days(self):
        api, call = _call_api()
        await api.billing_start_trial(12, days=30)
        call.assert_called_once_with("POST", "/support/billing/12/start-trial", json={"days": 30})

    @pytest.mark.parametrize("days", [0, 61, -1])
    async def test_start_trial_days_out_of_range(self, days):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="days"):
            await api.billing_start_trial(12, days=days)
        call.assert_not_called()

    async def test_end_trial(self):
        api, call = _call_api()
        await api.billing_end_trial(12)
        call.assert_called_once_with("POST", "/support/billing/12/end-trial")

    async def test_retry_payment(self):
        api, call = _call_api()
        await api.billing_retry_payment(12)
        call.assert_called_once_with("POST", "/support/billing/12/retry-payment")

    async def test_refund_full_is_explicit(self):
        api, call = _call_api()
        await api.billing_refund(12, full=True)
        call.assert_called_once_with("POST", "/support/billing/12/refund", params=None)

    async def test_refund_without_amount_or_full_is_refused(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="full"):
            await api.billing_refund(12)
        call.assert_not_called()

    async def test_refund_with_amount_and_full_is_refused(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="full"):
            await api.billing_refund(12, amount=100, full=True)
        call.assert_not_called()

    async def test_refund_partial_sends_cents_as_query(self):
        api, call = _call_api()
        await api.billing_refund(12, amount=2500)
        call.assert_called_once_with("POST", "/support/billing/12/refund", params={"amount": 2500})

    async def test_refund_rejects_non_positive_amount(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="amount"):
            await api.billing_refund(12, amount=0)
        call.assert_not_called()

    @pytest.mark.parametrize("amount", [-1, 2.5, "500", True])
    async def test_refund_rejects_non_int_or_negative_amount(self, amount):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="amount"):
            await api.billing_refund(12, amount=amount)
        call.assert_not_called()

    @pytest.mark.parametrize("bad", ["5", 2.5, True, None])
    async def test_ids_must_be_real_integers(self, bad):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.billing_end_trial(bad)
        call.assert_not_called()

    @pytest.mark.parametrize("days", ["7", 7.5, True])
    async def test_start_trial_days_must_be_an_int(self, days):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="days"):
            await api.billing_start_trial(12, days=days)
        call.assert_not_called()

    async def test_change_plan_defaults_to_now(self):
        api, call = _call_api()
        await api.billing_change_plan(12, 7)
        call.assert_called_once_with(
            "POST",
            "/support/billing/12/change-plan",
            json={"new_plan_id": 7, "when": "now"},
        )

    async def test_change_plan_period_end_with_storage(self):
        api, call = _call_api()
        await api.billing_change_plan(12, 7, when="period_end", storage_gb=500)
        call.assert_called_once_with(
            "POST",
            "/support/billing/12/change-plan",
            json={"new_plan_id": 7, "when": "period_end", "storage_gb": 500},
        )

    async def test_change_plan_rejects_unknown_when(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="when"):
            await api.billing_change_plan(12, 7, when="tomorrow")
        call.assert_not_called()

    async def test_cancel_subscription(self):
        api, call = _call_api()
        await api.billing_cancel_subscription(12, "period_end")
        call.assert_called_once_with(
            "POST", "/support/billing/12/cancel-subscription", json={"when": "period_end"}
        )

    async def test_cancel_subscription_rejects_unknown_when(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="when"):
            await api.billing_cancel_subscription(12, "later")
        call.assert_not_called()

    @pytest.mark.parametrize(
        "method",
        ["billing_start_trial", "billing_end_trial", "billing_retry_payment", "billing_refund"],
    )
    async def test_workspace_id_must_be_positive(self, method):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await getattr(api, method)(0)
        call.assert_not_called()


# ---------------------------------------------------------------------------
# Catalog reads
# ---------------------------------------------------------------------------


class TestCatalogReads:
    async def test_connector_bucket_impact(self):
        api, call = _call_api()
        await api.connector_bucket_impact(9, bucket="pro")
        call.assert_called_once_with(
            "GET", "/support/connectors/9/bucket-impact", params={"bucket": "pro"}
        )

    async def test_connector_bucket_impact_without_bucket(self):
        api, call = _call_api()
        await api.connector_bucket_impact(9)
        call.assert_called_once_with("GET", "/support/connectors/9/bucket-impact", params=None)

    async def test_connector_bucket_impact_invalid_id(self):
        api, _ = _call_api()
        with pytest.raises(MammothValidationError, match="connector_id"):
            await api.connector_bucket_impact(0)

    async def test_entitlement_registry(self):
        api, call = _call_api()
        await api.entitlement_registry()
        call.assert_called_once_with("GET", "/support/entitlements")

    async def test_plan_catalog(self):
        api, call = _call_api()
        await api.plan_catalog()
        call.assert_called_once_with("GET", "/support/plans/catalog")


# ---------------------------------------------------------------------------
# Deals
# ---------------------------------------------------------------------------


class TestDeals:
    async def test_list_and_get(self):
        api, call = _call_api()
        await api.deal_list()
        call.assert_called_with("GET", "/support/deals")
        await api.deal_get(4)
        call.assert_called_with("GET", "/support/deals/4")

    async def test_get_invalid_id(self):
        api, _ = _call_api()
        with pytest.raises(MammothValidationError, match="deal_id"):
            await api.deal_get(0)

    async def test_create_on_existing_workspace_sends_only_given_fields(self):
        api, call = _call_api({"id": 1, "workspace_id": 5})
        await api.deal_create(3, workspace_id=5, price=99.5, billing_interval="yearly")
        call.assert_called_once_with(
            "POST",
            "/support/deals",
            json={
                "base_plan_id": 3,
                "workspace_id": 5,
                "price": 99.5,
                "billing_interval": "yearly",
            },
        )

    async def test_create_with_new_workspace(self):
        api, call = _call_api()
        new_ws = {"name": "Acme", "user_email": "a@acme.test"}
        await api.deal_create(3, workspace_create=new_ws, status="trial", trial_end="2027-01-01")
        body = call.call_args.kwargs["json"]
        assert body["workspace_create"] == new_ws
        assert body["status"] == "trial"
        assert "workspace_id" not in body

    async def test_create_needs_exactly_one_workspace(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="exactly one"):
            await api.deal_create(3)
        with pytest.raises(MammothValidationError, match="exactly one"):
            await api.deal_create(3, workspace_id=1, workspace_create={"name": "x"})
        call.assert_not_called()

    async def test_update_sends_only_changed_fields(self):
        api, call = _call_api()
        await api.deal_update(4, notes="renewed", contact_email="")
        call.assert_called_once_with(
            "PUT", "/support/deals/4", json={"notes": "renewed", "contact_email": ""}
        )

    async def test_update_without_fields_is_rejected(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="at least one"):
            await api.deal_update(4)
        call.assert_not_called()

    async def test_activity_and_preview(self):
        api, call = _call_api()
        await api.deal_activity(4)
        call.assert_called_with("GET", "/support/deals/4/activity")
        await api.deal_preview_entitlement(4)
        call.assert_called_with("GET", "/support/deals/4/preview-entitlement")

    async def test_opt_in_keys_and_connectors(self):
        api, call = _call_api()
        await api.deal_opt_in(4, keys=["max_users"], connectors=["snowflake"])
        call.assert_called_once_with(
            "POST",
            "/support/deals/4/opt-in",
            json={"keys": ["max_users"], "connectors": ["snowflake"], "all": False},
        )

    async def test_opt_in_everything_is_sent_as_all(self):
        api, call = _call_api()
        await api.deal_opt_in(4, everything=True)
        call.assert_called_once_with(
            "POST", "/support/deals/4/opt-in", json={"keys": [], "connectors": [], "all": True}
        )

    async def test_opt_in_needs_something_to_release(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="everything"):
            await api.deal_opt_in(4)
        call.assert_not_called()

    async def test_move_to_partner_defaults_to_period_end(self):
        api, call = _call_api()
        await api.deal_move_to_partner(4, 2, 40.0, "monthly")
        call.assert_called_once_with(
            "POST",
            "/support/deals/4/move-to-partner",
            json={
                "partner_id": 2,
                "price": 40.0,
                "billing_interval": "monthly",
                "when": "period_end",
            },
        )

    async def test_move_to_partner_validates_inputs(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="price"):
            await api.deal_move_to_partner(4, 2, -1.0, "monthly")
        with pytest.raises(MammothValidationError, match="when"):
            await api.deal_move_to_partner(4, 2, 1.0, "monthly", when="never")
        with pytest.raises(MammothValidationError, match="partner_id"):
            await api.deal_move_to_partner(4, 0, 1.0, "monthly")
        call.assert_not_called()

    async def test_cancel_move_to_partner(self):
        api, call = _call_api()
        await api.deal_cancel_move_to_partner(4)
        call.assert_called_once_with("DELETE", "/support/deals/4/move-to-partner")


# ---------------------------------------------------------------------------
# Identities
# ---------------------------------------------------------------------------


class TestIdentities:
    async def test_list_without_filters(self):
        api, call = _call_api()
        await api.identity_list()
        call.assert_called_once_with(
            "GET", "/support/identities", params={"limit": 100, "offset": 0}
        )

    async def test_list_with_filters(self):
        api, call = _call_api()
        await api.identity_list(limit=20, offset=40, search="ann", sort="email", order="desc")
        call.assert_called_once_with(
            "GET",
            "/support/identities",
            params={"limit": 20, "offset": 40, "search": "ann", "sort": "email", "order": "desc"},
        )

    async def test_list_follows_the_pages_to_the_end(self):
        api, call = _call_api()
        call.side_effect = [
            {"users": [{"id": i} for i in range(100)]},
            {"users": [{"id": i} for i in range(100, 130)]},
        ]
        result = await api.identity_list()
        assert [u["id"] for u in result["users"]] == list(range(130))
        offsets = [c.kwargs["params"]["offset"] for c in call.call_args_list]
        assert offsets == [0, 100]

    async def test_list_stops_on_a_repeated_page(self):
        api, call = _call_api()
        page = {"users": [{"id": i} for i in range(100)]}
        call.side_effect = [page, page]
        result = await api.identity_list()
        assert len(result["users"]) == 100
        assert call.call_count == 2

    async def test_list_keeps_a_zero_offset(self):
        api, call = _call_api()
        await api.identity_list(offset=0)
        assert call.call_args.kwargs["params"]["offset"] == 0

    async def test_get(self):
        api, call = _call_api()
        await api.identity_get(77)
        call.assert_called_once_with("GET", "/support/identities/77")

    async def test_get_invalid_id(self):
        api, _ = _call_api()
        with pytest.raises(MammothValidationError, match="user_id"):
            await api.identity_get(0)


# ---------------------------------------------------------------------------
# Partners
# ---------------------------------------------------------------------------


class TestPartners:
    async def test_list_and_get(self):
        api, call = _call_api()
        await api.partner_list()
        call.assert_called_with("GET", "/support/partners")
        await api.partner_get(2)
        call.assert_called_with("GET", "/support/partners/2")

    async def test_create(self):
        api, call = _call_api()
        await api.partner_create(
            "Acme", contact_email="ops@acme.test", billing_method="send_invoice"
        )
        call.assert_called_once_with(
            "POST",
            "/support/partners",
            json={
                "name": "Acme",
                "contact_email": "ops@acme.test",
                "billing_method": "send_invoice",
            },
        )

    async def test_update_sends_only_given_fields_and_empty_clears(self):
        api, call = _call_api()
        await api.partner_update(2, status="inactive", notes="")
        call.assert_called_once_with(
            "PUT", "/support/partners/2", json={"status": "inactive", "notes": ""}
        )

    async def test_update_without_fields_is_rejected(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="at least one"):
            await api.partner_update(2)
        call.assert_not_called()

    async def test_reads(self):
        api, call = _call_api()
        await api.partner_activity(2)
        call.assert_called_with("GET", "/support/partners/2/activity")
        await api.partner_billing(2)
        call.assert_called_with("GET", "/support/partners/2/billing")
        await api.partner_invoices(2)
        call.assert_called_with("GET", "/support/partners/2/invoices")
        await api.partner_client_list(2)
        call.assert_called_with("GET", "/support/partners/2/workspaces")

    async def test_money_actions(self):
        api, call = _call_api()
        await api.partner_charge_invoices(2)
        call.assert_called_with("POST", "/support/partners/2/charge-invoices")
        await api.partner_send_payment_link(2)
        call.assert_called_with("POST", "/support/partners/2/send-payment-link")

    async def test_client_delete(self):
        api, call = _call_api()
        await api.partner_client_delete(2, 15)
        call.assert_called_once_with("DELETE", "/support/partners/2/workspaces/15")

    async def test_client_detach_sends_terms(self):
        api, call = _call_api()
        await api.partner_client_detach(
            2, 15, 120.0, "ap@client.test", billing_interval="yearly", notes="moved"
        )
        call.assert_called_once_with(
            "POST",
            "/support/partners/2/workspaces/15/detach",
            json={
                "price": 120.0,
                "contact_email": "ap@client.test",
                "billing_interval": "yearly",
                "notes": "moved",
            },
        )

    async def test_client_detach_price_must_be_positive(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="price"):
            await api.partner_client_detach(2, 15, 0, "ap@client.test")
        call.assert_not_called()

    async def test_client_cancel_detach(self):
        api, call = _call_api()
        await api.partner_client_cancel_detach(2, 15)
        call.assert_called_once_with("DELETE", "/support/partners/2/workspaces/15/detach")

    @pytest.mark.parametrize(
        ("method", "args"),
        [
            ("partner_get", (0,)),
            ("partner_client_delete", (2, 0)),
            ("partner_client_detach", (0, 1, 1.0, "a@b.test")),
            ("partner_client_cancel_detach", (0, 1)),
        ],
    )
    async def test_ids_must_be_positive(self, method, args):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="_id"):
            await getattr(api, method)(*args)
        call.assert_not_called()


# ---------------------------------------------------------------------------
# Admin home
# ---------------------------------------------------------------------------


class TestAdminHome:
    async def test_search_sends_q(self):
        api, call = _call_api({"results": []})
        await api.search("acme")
        call.assert_called_once_with("GET", "/support/search", params={"q": "acme"})

    async def test_triage_and_usage_tiles(self):
        api, call = _call_api()
        await api.triage()
        call.assert_called_with("GET", "/support/triage")
        await api.usage_tiles()
        call.assert_called_with("GET", "/support/usage-tiles")


# ---------------------------------------------------------------------------
# Workspace admin: activity, entitlement, archive, invites
# ---------------------------------------------------------------------------


class TestWorkspaceAdmin:
    async def test_reads(self):
        api, call = _call_api()
        await api.workspace_activity(8)
        call.assert_called_with("GET", "/support/workspaces/8/activity")
        await api.workspace_entitlement(8)
        call.assert_called_with("GET", "/support/workspaces/8/entitlement")
        await api.workspace_deal_seed(8)
        call.assert_called_with("GET", "/support/workspaces/8/deal-seed")
        await api.workspace_archive_info(8)
        call.assert_called_with("GET", "/support/workspaces/8/archive")

    async def test_chargebee_cancelled(self):
        api, call = _call_api()
        await api.workspace_chargebee_cancelled(8)
        call.assert_called_once_with("POST", "/support/workspaces/8/chargebee-cancelled")

    async def test_archive_sends_confirmation_and_storage_class(self):
        api, call = _call_api({"ledger": {}})
        await api.workspace_archive(8, "GLACIER_IR", "Acme Inc", reason="dormant")
        call.assert_called_once_with(
            "POST",
            "/support/workspaces/8/archive",
            json={
                "storage_class": "GLACIER_IR",
                "confirm_name": "Acme Inc",
                "cancel_billing": False,
                "reason": "dormant",
            },
        )

    async def test_archive_can_cancel_billing(self):
        api, call = _call_api()
        await api.workspace_archive(8, "DEEP_ARCHIVE", "Acme Inc", cancel_billing=True)
        assert call.call_args.kwargs["json"]["cancel_billing"] is True

    async def test_archive_validates_storage_class_and_name(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="storage_class"):
            await api.workspace_archive(8, "STANDARD", "Acme Inc")
        with pytest.raises(MammothValidationError, match="confirm_name"):
            await api.workspace_archive(8, "GLACIER_IR", "")
        call.assert_not_called()

    async def test_restore_archive(self):
        api, call = _call_api()
        await api.workspace_restore_archive(8)
        call.assert_called_once_with("POST", "/support/workspaces/8/restore")

    async def test_invite_cancel_and_resend(self):
        api, call = _call_api()
        await api.workspace_invite_cancel(8, 31)
        call.assert_called_with("DELETE", "/support/workspaces/8/users/invites/31")
        await api.workspace_invite_resend(8, 31)
        call.assert_called_with("POST", "/support/workspaces/8/users/invites/31/resend")

    async def test_invite_ids_must_be_positive(self):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="invite_id"):
            await api.workspace_invite_cancel(8, 0)
        with pytest.raises(MammothValidationError, match="workspace_id"):
            await api.workspace_invite_resend(0, 1)
        call.assert_not_called()


class TestBillingIntervalAndTypes:
    @pytest.mark.parametrize("interval", ["month", "year", "weekly"])
    async def test_a_billing_interval_outside_the_server_cycles_is_refused(self, interval):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="billing_interval"):
            await api.deal_create(3, workspace_id=5, price=1.0, billing_interval=interval)
        with pytest.raises(MammothValidationError, match="billing_interval"):
            await api.deal_update(3, billing_interval=interval)
        with pytest.raises(MammothValidationError, match="billing_interval"):
            await api.deal_move_to_partner(4, 2, 1.0, interval)
        with pytest.raises(MammothValidationError, match="billing_interval"):
            await api.partner_client_detach(2, 15, 1.0, "a@b.co", billing_interval=interval)
        call.assert_not_called()

    @pytest.mark.parametrize("interval", ["monthly", "yearly", "annual"])
    async def test_the_server_cycles_are_accepted(self, interval):
        api, call = _call_api()
        await api.deal_update(3, billing_interval=interval)
        assert call.call_args.kwargs["json"]["billing_interval"] == interval

    @pytest.mark.parametrize("price", ["9", True, None])
    async def test_a_non_number_price_is_a_validation_error(self, price):
        api, call = _call_api()
        with pytest.raises(MammothValidationError, match="price"):
            await api.deal_move_to_partner(4, 2, price, "monthly")
        with pytest.raises(MammothValidationError, match="price"):
            await api.partner_client_detach(2, 15, price, "a@b.co")
        call.assert_not_called()
