"""Support API client for Mammoth subscription and workspace administration.

Wraps the internal "support" endpoints used to administer subscription plans,
features, connectors, and their profiles, plus workspace and user
administration. Unlike most sub-clients, these endpoints operate on a target
``workspace_id`` / ``plan_id`` / etc. passed explicitly by the caller — they
are not scoped to the SDK client's own ``client.workspace_id``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

_ERR_ID = "`{name}` must be a positive integer, got {value}."
ERR_CUSTOMER_DETAILS_REQUIRED = (
    "Provide either `customer_id` (existing Chargebee customer) or the full set of "
    "`first_name`, `last_name`, `email`, `company_name` (new customer)."
)
ERR_STORAGE_TIERS_EMPTY = "`storage_tiers` must be a non-empty list."


def _check_id(name: str, value: int) -> None:
    """Validate that a path-id argument is a positive integer.

    Args:
        name: Name of the argument (used in the error message).
        value: The id value to check.

    Raises:
        MammothValidationError: If *value* is not a positive integer.
    """
    if value <= 0:
        raise MammothValidationError(_ERR_ID.format(name=name, value=value))


class SupportAPI:
    """Client for support/admin operations on subscriptions and workspaces.

    Access via ``client.support``::

        plans = client.support.plan_list()
        plan = client.support.plan_create(name="Pro", monthly_price=49.0, is_self_serve=True)
        client.support.workspace_suspend_access(1234, reason="Non-payment")

    Note:
        These are administrative endpoints. IDs such as ``workspace_id`` and
        ``plan_id`` identify the *target* resource being administered, not the
        SDK client's own workspace — they must always be passed explicitly.
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    # -- Plans ----------------------------------------------------------------

    def plan_list(self) -> dict[str, Any]:
        """List all subscription plans.

        Returns:
            Dict with the ``plans`` list.
        """
        return self._client._request_json("GET", "/subscription/plans")

    def plan_self_serve_list(self) -> dict[str, Any]:
        """List self-serve subscription plans.

        Returns:
            Dict with the ``plans`` list.
        """
        return self._client._request_json("GET", "/subscription/self-serve-plans")

    def plan_chargebee_list(self, resource: str = "plans") -> dict[str, Any]:
        """List available Chargebee plans/resources.

        Args:
            resource: Chargebee resource type to list (default ``"plans"``).

        Returns:
            Dict with the available Chargebee resources.
        """
        return self._client._request_json("GET", "/support/sms", params={"resource": resource})

    def plan_get(self, plan_id: int) -> dict[str, Any]:
        """Get details of a subscription plan.

        Args:
            plan_id: ID of the plan (must be a positive integer).

        Returns:
            Dict with plan details.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        return self._client._request_json("GET", f"/subscription/plans/{plan_id}")

    def plan_create(
        self,
        name: str,
        monthly_price: float,
        is_self_serve: bool,
        *,
        display_name: str | None = None,
        description: str | None = None,
        annual_price: float | None = None,
        annual_only: bool = False,
        trial_days: int | None = None,
        storage_amount: int = 0,
        max_storage: int | None = None,
        max_users: int | None = None,
        no_of_users: int | None = None,
        seat_price: float | None = None,
        number_of_tiers: int = 1,
        storage_block_size: int | None = None,
        tiers: list[dict[str, Any]] | None = None,
        connector_profile_id: int | None = None,
        feature_profile_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new subscription plan.

        Args:
            name: Plan name.
            monthly_price: Monthly price in USD.
            is_self_serve: Whether users can self-subscribe to this plan.
            display_name: Optional display name for the plan.
            description: Optional plan description.
            annual_price: Optional annual price in USD.
            annual_only: Whether the plan is annual-only (default ``False``).
            trial_days: Optional trial period in days.
            storage_amount: Included storage in GB (default ``0``).
            max_storage: Optional maximum storage in GB.
            max_users: Optional maximum number of users.
            no_of_users: Optional number of included users.
            seat_price: Optional price per additional user seat.
            number_of_tiers: Number of storage pricing tiers (default ``1``).
            storage_block_size: Optional storage block size in GB.
            tiers: Optional list of storage tier dicts (``{"gb": int, "price_per_gb": float}``).
            connector_profile_id: Optional connector profile ID to attach.
            feature_profile_id: Optional feature profile ID to attach.

        Returns:
            Dict with the created plan.
        """
        body: dict[str, Any] = {
            "name": name,
            "monthly_price": monthly_price,
            "is_self_serve": is_self_serve,
            "annual_only": annual_only,
            "storage_amount": storage_amount,
            "number_of_tiers": number_of_tiers,
        }
        if display_name is not None:
            body["display_name"] = display_name
        if description is not None:
            body["description"] = description
        if annual_price is not None:
            body["annual_price"] = annual_price
        if trial_days is not None:
            body["trial_days"] = trial_days
        if max_storage is not None:
            body["max_storage"] = max_storage
        if max_users is not None:
            body["max_users"] = max_users
        if no_of_users is not None:
            body["no_of_users"] = no_of_users
        if seat_price is not None:
            body["seat_price"] = seat_price
        if storage_block_size is not None:
            body["storage_block_size"] = storage_block_size
        if tiers is not None:
            body["tiers"] = tiers
        if connector_profile_id is not None:
            body["connector_profile_id"] = connector_profile_id
        if feature_profile_id is not None:
            body["feature_profile_id"] = feature_profile_id
        return self._client._request_json("POST", "/subscription/plans", json=body)

    def plan_update(
        self,
        plan_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        monthly_price: float | None = None,
        annual_price: float | None = None,
        annual_only: bool | None = None,
        is_self_serve: bool | None = None,
        trial_days: int | None = None,
        storage_amount: int | None = None,
        max_storage: int | None = None,
        max_users: int | None = None,
        no_of_users: int | None = None,
        seat_price: float | None = None,
        number_of_tiers: int | None = None,
        storage_block_size: int | None = None,
        tiers: list[dict[str, Any]] | None = None,
        connector_profile_id: int | None = None,
        feature_profile_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a subscription plan.

        Only fields explicitly given are included in the update.

        Args:
            plan_id: ID of the plan (must be a positive integer).
            name: New plan name.
            description: New plan description.
            monthly_price: New monthly price in USD.
            annual_price: New annual price in USD.
            annual_only: Whether the plan is annual-only.
            is_self_serve: Whether users can self-subscribe.
            trial_days: Trial period in days.
            storage_amount: Included storage in GB.
            max_storage: Maximum storage in GB.
            max_users: Maximum number of users.
            no_of_users: Number of included users.
            seat_price: Price per additional user seat.
            number_of_tiers: Number of storage pricing tiers.
            storage_block_size: Storage block size in GB.
            tiers: List of storage tier dicts (``{"gb": int, "price_per_gb": float}``).
            connector_profile_id: Connector profile ID to attach.
            feature_profile_id: Feature profile ID to attach.

        Returns:
            Dict with the updated plan.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        fields = {
            "name": name,
            "description": description,
            "monthly_price": monthly_price,
            "annual_price": annual_price,
            "annual_only": annual_only,
            "is_self_serve": is_self_serve,
            "trial_days": trial_days,
            "storage_amount": storage_amount,
            "max_storage": max_storage,
            "max_users": max_users,
            "no_of_users": no_of_users,
            "seat_price": seat_price,
            "number_of_tiers": number_of_tiers,
            "storage_block_size": storage_block_size,
            "tiers": tiers,
            "connector_profile_id": connector_profile_id,
            "feature_profile_id": feature_profile_id,
        }
        body = {k: v for k, v in fields.items() if v is not None}
        return self._client._request_json("PUT", f"/subscription/plans/{plan_id}", json=body)

    def plan_update_storage_tiers(
        self, plan_id: int, storage_tiers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Replace a plan's storage pricing tiers.

        Args:
            plan_id: ID of the plan (must be a positive integer).
            storage_tiers: Non-empty list of ``{"gb": int, "price_per_gb": float}`` dicts.

        Returns:
            Dict with the updated plan.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer, or
                *storage_tiers* is empty.
        """
        _check_id("plan_id", plan_id)
        if not storage_tiers:
            raise MammothValidationError(ERR_STORAGE_TIERS_EMPTY)
        return self._client._request_json(
            "PUT",
            f"/subscription/plans/{plan_id}/storage-tiers",
            json={"storage_tiers": storage_tiers},
        )

    def plan_delete(self, plan_id: int) -> dict[str, Any]:
        """Delete a subscription plan.

        Args:
            plan_id: ID of the plan (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        return self._client._request_json("DELETE", f"/subscription/plans/{plan_id}")

    def plan_archive(self, plan_id: int) -> dict[str, Any]:
        """Archive a subscription plan.

        Args:
            plan_id: ID of the plan (must be a positive integer).

        Returns:
            Dict with the archive result.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        return self._client._request_json("POST", f"/subscription/plans/{plan_id}/archive")

    # -- Features ---------------------------------------------------------------

    def feature_list(self) -> dict[str, Any]:
        """List all subscription features.

        Returns:
            Dict with the ``features`` list.
        """
        return self._client._request_json("GET", "/subscription/features")

    def feature_create(
        self,
        name: str,
        *,
        description: str | None = None,
        price_per_month: float = 0,
        enabled: bool = True,
        values: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new subscription feature.

        Args:
            name: Feature name.
            description: Optional feature description.
            price_per_month: Monthly price in USD (default ``0``).
            enabled: Whether the feature is enabled (default ``True``).
            values: Optional list of allowed values for the feature.

        Returns:
            Dict with the created feature.
        """
        body: dict[str, Any] = {
            "name": name,
            "price_per_month": price_per_month,
            "enabled": enabled,
        }
        if description is not None:
            body["description"] = description
        if values is not None:
            body["values"] = values
        return self._client._request_json("POST", "/subscription/features", json=body)

    def feature_update(
        self,
        feature_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        price_per_month: float | None = None,
        enabled: bool | None = None,
        values: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a subscription feature.

        Args:
            feature_id: ID of the feature (must be a positive integer).
            name: New feature name.
            description: New feature description.
            price_per_month: New monthly price in USD.
            enabled: Whether the feature is enabled.
            values: New list of allowed values for the feature.

        Returns:
            Dict with the updated feature.

        Raises:
            MammothValidationError: If *feature_id* is not a positive integer.
        """
        _check_id("feature_id", feature_id)
        fields = {
            "name": name,
            "description": description,
            "price_per_month": price_per_month,
            "enabled": enabled,
            "values": values,
        }
        body = {k: v for k, v in fields.items() if v is not None}
        return self._client._request_json("PUT", f"/subscription/features/{feature_id}", json=body)

    def feature_delete(self, feature_id: int) -> dict[str, Any]:
        """Delete a subscription feature.

        Args:
            feature_id: ID of the feature (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *feature_id* is not a positive integer.
        """
        _check_id("feature_id", feature_id)
        return self._client._request_json("DELETE", f"/subscription/features/{feature_id}")

    # -- Feature profiles ---------------------------------------------------------

    def feature_profile_list(self) -> dict[str, Any]:
        """List all feature profiles.

        Returns:
            Dict with the ``feature_profiles`` list.
        """
        return self._client._request_json("GET", "/subscription/feature-profiles")

    def feature_profile_create(
        self,
        name: str,
        *,
        description: str | None = None,
        features: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new feature profile.

        Args:
            name: Feature profile name.
            description: Optional feature profile description.
            features: Optional list of feature dicts (``{"feature_id": int,
                "price_per_month": float, "enabled": bool, "value": str}``).

        Returns:
            Dict with the created feature profile.
        """
        body: dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if features is not None:
            body["features"] = features
        return self._client._request_json("POST", "/subscription/feature-profiles", json=body)

    def feature_profile_update(
        self,
        profile_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        features: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update a feature profile.

        Args:
            profile_id: ID of the feature profile (must be a positive integer).
            name: New feature profile name.
            description: New feature profile description.
            features: New list of feature dicts (``{"feature_id": int,
                "price_per_month": float, "enabled": bool, "value": str}``).

        Returns:
            Dict with the updated feature profile.

        Raises:
            MammothValidationError: If *profile_id* is not a positive integer.
        """
        _check_id("profile_id", profile_id)
        fields = {"name": name, "description": description, "features": features}
        body = {k: v for k, v in fields.items() if v is not None}
        return self._client._request_json(
            "PUT", f"/subscription/feature-profiles/{profile_id}", json=body
        )

    def feature_profile_delete(self, profile_id: int) -> dict[str, Any]:
        """Delete a feature profile.

        Args:
            profile_id: ID of the feature profile (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *profile_id* is not a positive integer.
        """
        _check_id("profile_id", profile_id)
        return self._client._request_json("DELETE", f"/subscription/feature-profiles/{profile_id}")

    def feature_profile_add_feature(
        self,
        profile_id: int,
        feature_id: int,
        *,
        price_per_month: float = 0,
        enabled: bool = True,
        value: str | None = None,
    ) -> dict[str, Any]:
        """Add a feature to a feature profile.

        Args:
            profile_id: ID of the feature profile (must be a positive integer).
            feature_id: ID of the feature to add.
            price_per_month: Monthly price override in USD (default ``0``).
            enabled: Whether the feature is enabled (default ``True``).
            value: Optional value assigned to the feature in this profile.

        Returns:
            Dict with the added feature.

        Raises:
            MammothValidationError: If *profile_id* is not a positive integer.
        """
        _check_id("profile_id", profile_id)
        body: dict[str, Any] = {
            "feature_id": feature_id,
            "price_per_month": price_per_month,
            "enabled": enabled,
        }
        if value is not None:
            body["value"] = value
        return self._client._request_json(
            "POST", f"/subscription/feature-profiles/{profile_id}/features", json=body
        )

    # -- Connectors -----------------------------------------------------------

    def connector_list(self) -> dict[str, Any]:
        """List all subscription connectors.

        Returns:
            Dict with the ``connectors`` list.
        """
        return self._client._request_json("GET", "/subscription/connectors")

    def connector_create(
        self,
        name: str,
        *,
        description: str | None = None,
        price_per_month: float = 0,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Create a new subscription connector.

        Args:
            name: Connector name.
            description: Optional connector description.
            price_per_month: Monthly price in USD (default ``0``).
            enabled: Whether the connector is enabled (default ``True``).

        Returns:
            Dict with the created connector.
        """
        body: dict[str, Any] = {
            "name": name,
            "price_per_month": price_per_month,
            "enabled": enabled,
        }
        if description is not None:
            body["description"] = description
        return self._client._request_json("POST", "/subscription/connectors", json=body)

    def connector_update(
        self,
        connector_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        price_per_month: float | None = None,
        enabled: bool | None = None,
    ) -> dict[str, Any]:
        """Update a subscription connector.

        Args:
            connector_id: ID of the connector (must be a positive integer).
            name: New connector name.
            description: New connector description.
            price_per_month: New monthly price in USD.
            enabled: Whether the connector is enabled.

        Returns:
            Dict with the updated connector.

        Raises:
            MammothValidationError: If *connector_id* is not a positive integer.
        """
        _check_id("connector_id", connector_id)
        fields = {
            "name": name,
            "description": description,
            "price_per_month": price_per_month,
            "enabled": enabled,
        }
        body = {k: v for k, v in fields.items() if v is not None}
        return self._client._request_json(
            "PUT", f"/subscription/connectors/{connector_id}", json=body
        )

    def connector_delete(self, connector_id: int) -> dict[str, Any]:
        """Delete a subscription connector.

        Args:
            connector_id: ID of the connector (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *connector_id* is not a positive integer.
        """
        _check_id("connector_id", connector_id)
        return self._client._request_json("DELETE", f"/subscription/connectors/{connector_id}")

    # -- Connector profiles -----------------------------------------------------

    def connector_profile_list(self) -> dict[str, Any]:
        """List all connector profiles.

        Returns:
            Dict with the ``connector_profiles`` list.
        """
        return self._client._request_json("GET", "/subscription/connector-profiles")

    def connector_profile_create(
        self,
        name: str,
        *,
        description: str | None = None,
        connectors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new connector profile.

        Args:
            name: Connector profile name.
            description: Optional connector profile description.
            connectors: Optional list of connector dicts (``{"connector_id": int,
                "price_per_month": float, "enabled": bool}``).

        Returns:
            Dict with the created connector profile.
        """
        body: dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        if connectors is not None:
            body["connectors"] = connectors
        return self._client._request_json("POST", "/subscription/connector-profiles", json=body)

    def connector_profile_update(
        self,
        profile_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        connectors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update a connector profile.

        Args:
            profile_id: ID of the connector profile (must be a positive integer).
            name: New connector profile name.
            description: New connector profile description.
            connectors: New list of connector dicts (``{"connector_id": int,
                "price_per_month": float, "enabled": bool}``).

        Returns:
            Dict with the updated connector profile.

        Raises:
            MammothValidationError: If *profile_id* is not a positive integer.
        """
        _check_id("profile_id", profile_id)
        fields = {"name": name, "description": description, "connectors": connectors}
        body = {k: v for k, v in fields.items() if v is not None}
        return self._client._request_json(
            "PUT", f"/subscription/connector-profiles/{profile_id}", json=body
        )

    def connector_profile_delete(self, profile_id: int) -> dict[str, Any]:
        """Delete a connector profile.

        Args:
            profile_id: ID of the connector profile (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *profile_id* is not a positive integer.
        """
        _check_id("profile_id", profile_id)
        return self._client._request_json(
            "DELETE", f"/subscription/connector-profiles/{profile_id}"
        )

    def connector_profile_add_connector(
        self,
        profile_id: int,
        connector_id: int,
        *,
        price_per_month: float = 0,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Add a connector to a connector profile.

        Args:
            profile_id: ID of the connector profile (must be a positive integer).
            connector_id: ID of the connector to add.
            price_per_month: Monthly price override in USD (default ``0``).
            enabled: Whether the connector is enabled (default ``True``).

        Returns:
            Dict with the added connector.

        Raises:
            MammothValidationError: If *profile_id* is not a positive integer.
        """
        _check_id("profile_id", profile_id)
        body: dict[str, Any] = {
            "connector_id": connector_id,
            "price_per_month": price_per_month,
            "enabled": enabled,
        }
        return self._client._request_json(
            "POST", f"/subscription/connector-profiles/{profile_id}/connectors", json=body
        )

    # -- Workspace subscriptions ------------------------------------------------

    def subscription_get(self, workspace_id: int, fields: str | None = None) -> dict[str, Any]:
        """Get the Chargebee subscription details for a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            fields: Optional comma-separated list of fields to return.

        Returns:
            Dict with subscription details.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        return self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}/sms", params=params or None
        )

    def subscription_create(
        self,
        workspace_id: int,
        plan_id: str,
        *,
        customer_id: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        company_name: str | None = None,
    ) -> dict[str, Any]:
        """Register a workspace with a Chargebee subscription.

        Provide either *customer_id* (an existing Chargebee customer) or the
        full set of *first_name*, *last_name*, *email*, *company_name* (to
        create a new customer).

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            plan_id: Chargebee plan ID to subscribe to.
            customer_id: ID of an existing Chargebee customer.
            first_name: New customer's first name.
            last_name: New customer's last name.
            email: New customer's email.
            company_name: New customer's company name.

        Returns:
            Dict with the registration job info.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer,
                or neither *customer_id* nor the full new-customer field set is given.
        """
        _check_id("workspace_id", workspace_id)
        has_new_customer = all([first_name, last_name, email, company_name])
        if not customer_id and not has_new_customer:
            raise MammothValidationError(ERR_CUSTOMER_DETAILS_REQUIRED)
        body: dict[str, Any] = {"plan_id": plan_id}
        if customer_id is not None:
            body["customer_id"] = customer_id
        if first_name is not None:
            body["first_name"] = first_name
        if last_name is not None:
            body["last_name"] = last_name
        if email is not None:
            body["email"] = email
        if company_name is not None:
            body["company_name"] = company_name
        return self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/sms", json=body
        )

    def subscription_update(self, workspace_id: int, subscription_id: str) -> dict[str, Any]:
        """Update a workspace's Chargebee subscription id.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            subscription_id: New Chargebee subscription id.

        Returns:
            Dict with the update result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        body = {"patch": [{"op": "replace", "path": "subscription_id", "value": subscription_id}]}
        return self._client._request_json(
            "PATCH", f"/support/workspaces/{workspace_id}/sms", json=body
        )

    # -- Users (global) -----------------------------------------------------------

    def user_register(
        self,
        email: str,
        first_name: str,
        last_name: str,
        verified: bool,
        is_registration: bool | None = None,
    ) -> dict[str, Any]:
        """Register a new user.

        Args:
            email: Email of the user to register.
            first_name: First name of the user.
            last_name: Last name of the user.
            verified: Whether the user is verified.
            is_registration: Whether the request originates from registration.

        Returns:
            Dict with the registered user info.
        """
        body: dict[str, Any] = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "verified": verified,
        }
        if is_registration is not None:
            body["is_registration"] = is_registration
        return self._client._request_json("POST", "/support/users", json=body)

    def user_update(
        self, email: str, verified: bool, is_registration: bool | None = None
    ) -> dict[str, Any]:
        """Update a user's verification status.

        Args:
            email: Email of the user to update.
            verified: New verified status.
            is_registration: Whether the request originates from registration.

        Returns:
            Dict with the update result.
        """
        value: dict[str, Any] = {"email": email, "verified": verified}
        if is_registration is not None:
            value["is_registration"] = is_registration
        body = {"patch": [{"op": "replace", "path": "verified", "value": value}]}
        return self._client._request_json("PATCH", "/support/users", json=body)

    def user_list_all(
        self,
        fields: str | None = None,
        sort: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List users across workspaces.

        Args:
            fields: Optional comma-separated list of fields to return.
            sort: Optional sort spec, e.g. ``"(email:asc)"``.
            offset: Number of results to skip.
            limit: Maximum number of results.

        Returns:
            Dict with the ``users`` list and pagination info.
        """
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        if sort is not None:
            params["sort"] = sort
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        return self._client._request_json("GET", "/settings/users", params=params or None)

    # -- Ownership transfer (settings) -------------------------------------------

    def ownership_transfer(
        self,
        workspace_id: int,
        user_id: int,
        new_role: str = "workspace_owner",
        remove_role: str | None = None,
    ) -> dict[str, Any]:
        """Transfer ownership of a workspace to another user.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            user_id: ID of the user to transfer the role to.
            new_role: Role to assign to *user_id* (default ``"workspace_owner"``).
            remove_role: Optional role to remove from the previous holder.

        Returns:
            Dict with the transfer result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        value: dict[str, Any] = {
            "workspace_id": workspace_id,
            "user_id": user_id,
            "new_role": new_role,
        }
        if remove_role is not None:
            value["remove_role"] = remove_role
        body = {"patches": [{"op": "replace", "path": "role", "value": value}]}
        return self._client._request_json("PATCH", "/settings/users", json=body)

    # -- Workspaces (support/admin) -----------------------------------------------

    def workspace_list(self) -> dict[str, Any]:
        """List all workspaces visible to the current admin/support user.

        Returns:
            Dict with the ``workspaces`` list (or ``instance_types``, depending
            on the server response variant).
        """
        return self._client._request_json("GET", "/support/workspaces")

    def workspace_get(self, workspace_id: int, fields: str | None = None) -> dict[str, Any]:
        """Get details of a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            fields: Optional comma-separated list of fields to return.

        Returns:
            Dict with workspace details.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        params: dict[str, Any] = {}
        if fields is not None:
            params["fields"] = fields
        return self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}", params=params or None
        )

    def workspace_create(
        self,
        name: str,
        user_email: str,
        payment_frequency: str,
        *,
        plan_id: int | None = None,
        origin: str | None = None,
        is_verified: bool = True,
        is_registration: bool = False,
        file_id: str | None = None,
        table_number: int | None = None,
        plan_create: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new workspace.

        Args:
            name: Name of the workspace to create.
            user_email: Email of the owning user.
            payment_frequency: Billing frequency (e.g. ``"monthly"``, ``"yearly"``).
            plan_id: Optional plan ID to subscribe the workspace to.
            origin: Optional origin of the request (e.g. ``"WEBSITE_PLAN_SELECTION"``).
            is_verified: Whether the owning user is verified (default ``True``).
            is_registration: Whether this is a registration flow (default ``False``).
            file_id: Optional file ID to seed the workspace with.
            table_number: Optional table number to seed the workspace with.
            plan_create: Optional inline plan-creation payload (same shape as
                :meth:`plan_create`'s body) used to create a new plan before
                creating the workspace.

        Returns:
            Dict with the created workspace.
        """
        body: dict[str, Any] = {
            "name": name,
            "user_email": user_email,
            "payment_frequency": payment_frequency,
            "is_verified": is_verified,
            "is_registration": is_registration,
        }
        if plan_id is not None:
            body["plan_id"] = plan_id
        if origin is not None:
            body["origin"] = origin
        if file_id is not None:
            body["file_id"] = file_id
        if table_number is not None:
            body["table_number"] = table_number
        if plan_create is not None:
            body["plan_create"] = plan_create
        return self._client._request_json("POST", "/support/workspaces", json=body)

    def workspace_update(
        self,
        workspace_id: int,
        name: str,
        payment_frequency: str,
        plan_id: int,
        *,
        plan_create: dict[str, Any] | None = None,
        plan_update: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a workspace's details and/or subscription.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            name: New workspace name.
            payment_frequency: New billing frequency (e.g. ``"monthly"``, ``"yearly"``).
            plan_id: Plan ID to switch the workspace subscription to.
            plan_create: Optional inline plan-creation payload (same shape as
                :meth:`plan_create`'s body); creates a new plan and switches
                the workspace to it.
            plan_update: Optional inline plan-update payload (same shape as
                :meth:`plan_update`'s body); updates the plan identified by
                *plan_id*.

        Returns:
            Dict with the updated workspace.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        body: dict[str, Any] = {
            "name": name,
            "payment_frequency": payment_frequency,
            "plan_id": plan_id,
        }
        if plan_create is not None:
            body["plan_create"] = plan_create
        if plan_update is not None:
            body["plan_update"] = plan_update
        return self._client._request_json("PATCH", f"/support/workspaces/{workspace_id}", json=body)

    def workspace_delete(self, workspace_id: int) -> dict[str, Any]:
        """Delete a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return self._client._request_json("DELETE", f"/support/workspaces/{workspace_id}")

    def workspace_suspend_access(
        self, workspace_id: int, reason: str | None = None
    ) -> dict[str, Any]:
        """Suspend user access to a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            reason: Optional reason recorded with the suspension (for support).

        Returns:
            Dict with the suspension result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        body: dict[str, Any] = {}
        if reason is not None:
            body["reason"] = reason
        return self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/suspend-access", json=body
        )

    def workspace_restore_access(self, workspace_id: int) -> dict[str, Any]:
        """Restore user access to a suspended workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with the restoration result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/restore-access"
        )

    # -- Workspace users (support/admin) ------------------------------------------

    def workspace_user_list(
        self,
        workspace_id: int,
        limit: int | None = None,
        offset: int | None = None,
        fields: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List users in a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            limit: Maximum number of results.
            offset: Number of results to skip.
            fields: Optional comma-separated list of fields to return.
            sort: Optional sort spec, e.g. ``"(email:asc)"``.

        Returns:
            Dict with the ``users`` list and pagination info.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if fields is not None:
            params["fields"] = fields
        if sort is not None:
            params["sort"] = sort
        return self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}/users", params=params or None
        )

    def workspace_user_add(
        self,
        workspace_id: int,
        email: str,
        role: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict[str, Any]:
        """Add a user to a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            email: Email of the user to add.
            role: Role to assign, one of ``"workspace_member"``,
                ``"workspace_admin"``, ``"workspace_owner"``, ``"workspace_guest"``.
            first_name: Optional first name (used if the user does not yet exist).
            last_name: Optional last name (used if the user does not yet exist).

        Returns:
            Dict with the added user.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        body: dict[str, Any] = {"email": email, "role": role}
        if first_name is not None:
            body["first_name"] = first_name
        if last_name is not None:
            body["last_name"] = last_name
        return self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/users", json=body
        )

    def workspace_user_remove(self, workspace_id: int, user_id: int) -> dict[str, Any]:
        """Remove a user from a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            user_id: ID of the user to remove.

        Returns:
            Dict with the removal result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return self._client._request_json(
            "DELETE", f"/support/workspaces/{workspace_id}/users/{user_id}"
        )

    def workspace_user_transfer(
        self,
        workspace_id: int,
        user_id: int,
        role: str,
        remove_role: str | None = None,
    ) -> dict[str, Any]:
        """Transfer/change a user's role within a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            user_id: ID of the user whose role is being changed.
            role: New role to assign to *user_id*.
            remove_role: Role being removed from *user_id* (or from the
                previous holder), if applicable.

        Returns:
            Dict with the transfer result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        value = {"user_id": user_id, "role": role, "remove_role": remove_role}
        body = {"patch": [{"op": "replace", "path": "role", "value": value}]}
        return self._client._request_json(
            "PATCH", f"/support/workspaces/{workspace_id}/users", json=body
        )
