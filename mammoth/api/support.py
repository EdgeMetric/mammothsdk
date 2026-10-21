"""Support API client for Mammoth subscription and workspace administration.

Wraps the internal "support" endpoints used to administer subscription plans,
features, connectors, and their profiles, plus workspace and user
administration. Unlike most sub-clients, these endpoints operate on a target
``workspace_id`` / ``plan_id`` / etc. passed explicitly by the caller — they
are not scoped to the SDK client's own ``client.workspace_id``.
"""

from __future__ import annotations

import asyncio
import base64
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from mammoth.api.dashboards import _write_bytes_atomic
from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

_ERR_ID = "`{name}` must be a positive integer, got {value}."
ERR_CUSTOMER_DETAILS_REQUIRED = (
    "Provide either `customer_id` (existing Chargebee customer) or the full set of "
    "`first_name`, `last_name`, `email`, `company_name` (new customer)."
)
WORKSPACE_LIST_PAGE_SIZE = 100
WORKSPACE_LIST_MAX_PAGES = 1000
WARN_CONNECTOR_PRICE_IGNORED = (
    "`price_per_month` is ignored for subscription connectors: the server dropped the "
    "field (connectors are access, not a priced line item), so it is no longer sent."
)
ERR_STORAGE_TIERS_EMPTY = "`storage_tiers` must be a non-empty list."
ERR_STORAGE_OPTION_NO_CHANGE = "Provide at least one of storage_gb, monthly_price, annual_price."
ERR_SLUG_EMPTY = "`slug` must be a non-empty template slug."
ERR_TEMPLATE_CHANGES_EMPTY = "`changes` must be a non-empty mapping of filing fields."

TRIAL_DAYS_MIN = 1
TRIAL_DAYS_MAX = 60
ERR_TRIAL_DAYS = f"`days` must be between {TRIAL_DAYS_MIN} and {TRIAL_DAYS_MAX}."
BILLING_WHEN = ("now", "period_end")
ERR_BILLING_WHEN = '`when` must be "now" or "period_end", got {value!r}.'
MOVE_WHEN = ("period_end", "now")
ERR_MOVE_WHEN = '`when` must be "period_end" or "now", got {value!r}.'
ERR_PRICE_NEGATIVE = "`price` must be 0 or more."
ERR_PRICE_POSITIVE = "`price` must be above 0."
BILLING_INTERVALS = ("monthly", "yearly", "annual")
ERR_BILLING_INTERVAL = (
    '`billing_interval` must be one of "monthly", "yearly" or "annual", got {value!r}.'
)
ERR_REFUND_AMOUNT = (
    "Give either `amount` (a partial refund in cents) or `full=True`, not both or neither."
)
IDENTITY_LIST_PAGE_SIZE = 100
IDENTITY_LIST_MAX_PAGES = 1000
ERR_DEAL_WORKSPACE = "Provide exactly one of `workspace_id` or `workspace_create`."
ERR_DEAL_NO_CHANGE = "Provide at least one deal field to change."
ERR_DEAL_OPT_IN_EMPTY = "Provide `keys`, `connectors` or `everything=True`."
ERR_PARTNER_NO_CHANGE = "Provide at least one partner field to change."
ARCHIVE_STORAGE_CLASSES = ("GLACIER_IR", "DEEP_ARCHIVE")
ERR_STORAGE_CLASS = '`storage_class` must be "GLACIER_IR" or "DEEP_ARCHIVE", got {value!r}.'
ERR_CONFIRM_NAME = "`confirm_name` must be the workspace name, typed to confirm."

#: Root of the curated-template admin routes (dashboards v3).
_TEMPLATE_ADMIN = "/dashboards/v3/templates/admin"


def _template_path(slug: str, suffix: str = "") -> str:
    """One curated template's admin route, its slug path-encoded."""
    if not slug:
        raise MammothValidationError(ERR_SLUG_EMPTY)
    return f"{_TEMPLATE_ADMIN}/{quote(slug, safe='')}{suffix}"


def _local_file(file: str | Path) -> Path:
    """The local file a multipart upload sends, or a validation error."""
    path = Path(file)
    if not path.is_file():
        raise MammothValidationError(f"File not found: {path}")
    return path


def _drop_none(**fields: Any) -> dict[str, Any]:
    """The fields that were given: every keyword whose value is not ``None``."""
    return {key: value for key, value in fields.items() if value is not None}


def _check_id(name: str, value: int) -> None:
    """Validate that a path-id argument is a positive integer.

    Args:
        name: Name of the argument (used in the error message).
        value: The id value to check.

    Raises:
        MammothValidationError: If *value* is not a positive integer.
    """
    if not _is_int(value) or value <= 0:
        raise MammothValidationError(_ERR_ID.format(name=name, value=value))


def _is_int(value: Any) -> bool:
    """True for a real integer (``bool`` is not one)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    """True for an ``int`` or ``float`` (``bool`` is not one)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_interval(value: str | None) -> None:
    """Validate a billing interval against the cycles the server accepts."""
    if value is not None and value not in BILLING_INTERVALS:
        raise MammothValidationError(ERR_BILLING_INTERVAL.format(value=value))


class SupportAPI:
    """Client for support/admin operations on subscriptions and workspaces.

    Access via ``client.support``::

        plans = await client.support.plan_list()
        plan = await client.support.plan_create(name="Pro", monthly_price=49.0, is_self_serve=True)
        await client.support.workspace_suspend_access(1234, reason="Non-payment")

    Note:
        These are administrative endpoints. IDs such as ``workspace_id`` and
        ``plan_id`` identify the *target* resource being administered, not the
        SDK client's own workspace — they must always be passed explicitly.
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    # -- Plans ----------------------------------------------------------------

    async def plan_list(self) -> dict[str, Any]:
        """List all subscription plans.

        Returns:
            Dict with the ``plans`` list.
        """
        return await self._client._request_json("GET", "/subscription/plans")

    async def plan_self_serve_list(self) -> dict[str, Any]:
        """List self-serve subscription plans.

        Returns:
            Dict with the ``plans`` list.
        """
        return await self._client._request_json("GET", "/subscription/self-serve-plans")

    async def plan_chargebee_list(self, resource: str = "plans") -> dict[str, Any]:
        """List available Chargebee plans/resources.

        Args:
            resource: Chargebee resource type to list (default ``"plans"``).

        Returns:
            Dict with the available Chargebee resources.
        """
        return await self._client._request_json(
            "GET", "/support/sms", params={"resource": resource}
        )

    async def plan_get(self, plan_id: int) -> dict[str, Any]:
        """Get details of a subscription plan.

        Args:
            plan_id: ID of the plan (must be a positive integer).

        Returns:
            Dict with plan details.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        return await self._client._request_json("GET", f"/subscription/plans/{plan_id}")

    async def plan_create(
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
        return await self._client._request_json("POST", "/subscription/plans", json=body)

    async def plan_update(
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
        return await self._client._request_json("PUT", f"/subscription/plans/{plan_id}", json=body)

    async def plan_update_storage_tiers(
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
        return await self._client._request_json(
            "PUT",
            f"/subscription/plans/{plan_id}/storage-tiers",
            json={"storage_tiers": storage_tiers},
        )

    async def plan_delete(self, plan_id: int) -> dict[str, Any]:
        """Delete a subscription plan.

        Args:
            plan_id: ID of the plan (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        return await self._client._request_json("DELETE", f"/subscription/plans/{plan_id}")

    async def plan_archive(self, plan_id: int) -> dict[str, Any]:
        """Archive a subscription plan.

        Args:
            plan_id: ID of the plan (must be a positive integer).

        Returns:
            Dict with the archive result.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        return await self._client._request_json("POST", f"/subscription/plans/{plan_id}/archive")

    async def plan_unarchive(self, plan_id: int) -> dict[str, Any]:
        """Unarchive a subscription plan (undo :meth:`plan_archive`).

        Args:
            plan_id: ID of the plan (must be a positive integer).

        Returns:
            Dict with ``plan`` and ``message``.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        return await self._client._request_json("POST", f"/subscription/plans/{plan_id}/unarchive")

    # -- Plan storage options -------------------------------------------------

    async def plan_storage_option_list(self, plan_id: int) -> dict[str, Any]:
        """List every purchasable storage size of a plan, archived ones included.

        Args:
            plan_id: ID of the plan (must be a positive integer).

        Returns:
            Dict with ``storage_options``.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        return await self._client._request_json(
            "GET", f"/subscription/plans/{plan_id}/storage-options"
        )

    async def plan_storage_option_create(
        self, plan_id: int, storage_gb: int, monthly_price: float, annual_price: float
    ) -> dict[str, Any]:
        """Add a purchasable storage size to an inline-pricing plan.

        Args:
            plan_id: ID of the plan (must be a positive integer).
            storage_gb: TOTAL storage the option grants, in GB (not an increment).
            monthly_price: Monthly add in USD on top of the plan price.
            annual_price: Annual add in USD on top of the plan price.

        Returns:
            Dict with ``storage_option`` and ``message``.

        Raises:
            MammothValidationError: If *plan_id* is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        body = {
            "storage_gb": storage_gb,
            "monthly_price": monthly_price,
            "annual_price": annual_price,
        }
        return await self._client._request_json(
            "POST", f"/subscription/plans/{plan_id}/storage-options", json=body
        )

    async def plan_storage_option_update(
        self,
        plan_id: int,
        option_id: int,
        storage_gb: int | None = None,
        monthly_price: float | None = None,
        annual_price: float | None = None,
    ) -> dict[str, Any]:
        """Re-price a storage option, or move it to a different size.

        Args:
            plan_id: ID of the plan (must be a positive integer).
            option_id: ID of the storage option (must be a positive integer).
            storage_gb: New TOTAL storage in GB.
            monthly_price: New monthly add in USD.
            annual_price: New annual add in USD.

        Returns:
            Dict with ``storage_option`` and ``message``.

        Raises:
            MammothValidationError: If an id is not a positive integer, or no
                field is given.
        """
        _check_id("plan_id", plan_id)
        _check_id("option_id", option_id)
        fields = {
            "storage_gb": storage_gb,
            "monthly_price": monthly_price,
            "annual_price": annual_price,
        }
        body = {key: value for key, value in fields.items() if value is not None}
        if not body:
            raise MammothValidationError(ERR_STORAGE_OPTION_NO_CHANGE)
        return await self._client._request_json(
            "PUT", f"/subscription/plans/{plan_id}/storage-options/{option_id}", json=body
        )

    async def plan_storage_option_archive(self, plan_id: int, option_id: int) -> dict[str, Any]:
        """Archive a storage option so it can no longer be chosen.

        Never a hard delete: subscriptions already billed at that size keep it.

        Args:
            plan_id: ID of the plan (must be a positive integer).
            option_id: ID of the storage option (must be a positive integer).

        Returns:
            Dict with ``storage_option`` and ``message``.

        Raises:
            MammothValidationError: If an id is not a positive integer.
        """
        _check_id("plan_id", plan_id)
        _check_id("option_id", option_id)
        return await self._client._request_json(
            "DELETE", f"/subscription/plans/{plan_id}/storage-options/{option_id}"
        )

    # -- Features ---------------------------------------------------------------

    async def feature_list(self) -> dict[str, Any]:
        """List all subscription features.

        Returns:
            Dict with the ``features`` list.
        """
        return await self._client._request_json("GET", "/subscription/features")

    async def feature_create(
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
        return await self._client._request_json("POST", "/subscription/features", json=body)

    async def feature_update(
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
        return await self._client._request_json(
            "PUT", f"/subscription/features/{feature_id}", json=body
        )

    async def feature_delete(self, feature_id: int) -> dict[str, Any]:
        """Delete a subscription feature.

        Args:
            feature_id: ID of the feature (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *feature_id* is not a positive integer.
        """
        _check_id("feature_id", feature_id)
        return await self._client._request_json("DELETE", f"/subscription/features/{feature_id}")

    # -- Feature profiles ---------------------------------------------------------

    async def feature_profile_list(self) -> dict[str, Any]:
        """List all feature profiles.

        Returns:
            Dict with the ``feature_profiles`` list.
        """
        return await self._client._request_json("GET", "/subscription/feature-profiles")

    async def feature_profile_create(
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
        return await self._client._request_json("POST", "/subscription/feature-profiles", json=body)

    async def feature_profile_update(
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
        return await self._client._request_json(
            "PUT", f"/subscription/feature-profiles/{profile_id}", json=body
        )

    async def feature_profile_delete(self, profile_id: int) -> dict[str, Any]:
        """Delete a feature profile.

        Args:
            profile_id: ID of the feature profile (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *profile_id* is not a positive integer.
        """
        _check_id("profile_id", profile_id)
        return await self._client._request_json(
            "DELETE", f"/subscription/feature-profiles/{profile_id}"
        )

    async def feature_profile_add_feature(
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
        return await self._client._request_json(
            "POST", f"/subscription/feature-profiles/{profile_id}/features", json=body
        )

    # -- Connectors -----------------------------------------------------------

    async def connector_list(self) -> dict[str, Any]:
        """List all subscription connectors.

        Returns:
            Dict with the ``connectors`` list.
        """
        return await self._client._request_json("GET", "/subscription/connectors")

    async def connector_create(
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
            price_per_month: Deprecated and ignored. The server no longer has a
                price on connectors, so the SDK does not send it (a non-zero value
                warns). Kept so existing calls still work.
            enabled: Whether the connector is enabled (default ``True``).

        Returns:
            Dict with the created connector.
        """
        if price_per_month:
            warnings.warn(WARN_CONNECTOR_PRICE_IGNORED, DeprecationWarning, stacklevel=2)
        body: dict[str, Any] = {"name": name, "enabled": enabled}
        if description is not None:
            body["description"] = description
        return await self._client._request_json("POST", "/subscription/connectors", json=body)

    async def connector_update(
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
            price_per_month: Deprecated and ignored. The server no longer has a
                price on connectors, so the SDK does not send it (a value warns).
                Kept so existing calls still work.
            enabled: Whether the connector is enabled.

        Returns:
            Dict with the updated connector.

        Raises:
            MammothValidationError: If *connector_id* is not a positive integer.
        """
        _check_id("connector_id", connector_id)
        if price_per_month is not None:
            warnings.warn(WARN_CONNECTOR_PRICE_IGNORED, DeprecationWarning, stacklevel=2)
        fields = {
            "name": name,
            "description": description,
            "enabled": enabled,
        }
        body = {k: v for k, v in fields.items() if v is not None}
        return await self._client._request_json(
            "PUT", f"/subscription/connectors/{connector_id}", json=body
        )

    async def connector_delete(self, connector_id: int) -> dict[str, Any]:
        """Delete a subscription connector.

        Args:
            connector_id: ID of the connector (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *connector_id* is not a positive integer.
        """
        _check_id("connector_id", connector_id)
        return await self._client._request_json(
            "DELETE", f"/subscription/connectors/{connector_id}"
        )

    # -- Connector profiles -----------------------------------------------------

    async def connector_profile_list(self) -> dict[str, Any]:
        """List all connector profiles.

        Returns:
            Dict with the ``connector_profiles`` list.
        """
        return await self._client._request_json("GET", "/subscription/connector-profiles")

    async def connector_profile_create(
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
        return await self._client._request_json(
            "POST", "/subscription/connector-profiles", json=body
        )

    async def connector_profile_update(
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
        return await self._client._request_json(
            "PUT", f"/subscription/connector-profiles/{profile_id}", json=body
        )

    async def connector_profile_delete(self, profile_id: int) -> dict[str, Any]:
        """Delete a connector profile.

        Args:
            profile_id: ID of the connector profile (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *profile_id* is not a positive integer.
        """
        _check_id("profile_id", profile_id)
        return await self._client._request_json(
            "DELETE", f"/subscription/connector-profiles/{profile_id}"
        )

    async def connector_profile_add_connector(
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
        return await self._client._request_json(
            "POST", f"/subscription/connector-profiles/{profile_id}/connectors", json=body
        )

    # -- Workspace subscriptions ------------------------------------------------

    async def subscription_get(
        self, workspace_id: int, fields: str | None = None
    ) -> dict[str, Any]:
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
        return await self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}/sms", params=params or None
        )

    async def subscription_create(
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
        return await self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/sms", json=body
        )

    async def subscription_update(self, workspace_id: int, subscription_id: str) -> dict[str, Any]:
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
        return await self._client._request_json(
            "PATCH", f"/support/workspaces/{workspace_id}/sms", json=body
        )

    # -- Users (global) -----------------------------------------------------------

    async def user_register(
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
        return await self._client._request_json("POST", "/support/users", json=body)

    async def user_update(
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
        return await self._client._request_json("PATCH", "/support/users", json=body)

    async def user_list_all(
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
        return await self._client._request_json("GET", "/settings/users", params=params or None)

    # -- Ownership transfer (settings) -------------------------------------------

    async def ownership_transfer(
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
        return await self._client._request_json("PATCH", "/settings/users", json=body)

    # -- Workspaces (support/admin) -----------------------------------------------

    async def workspace_list(self) -> dict[str, Any]:
        """List all workspaces visible to the current admin/support user.

        The route pages its answer (``limit`` defaults to 50, at most 100), so this
        follows the pages until the list is complete. A backend that ignores paging
        and answers with the whole list is read once more and stops on the repeat.

        Returns:
            Dict with the ``workspaces`` list (or ``instance_types``, depending
            on the server response variant). The release backend answers this
            route with a bare JSON array, which is wrapped as ``{"workspaces":
            [...]}`` so callers get the usual dict shape.
        """
        workspaces: list[Any] = []
        seen: set[Any] = set()
        previous: list[Any] | None = None
        for page_number in range(WORKSPACE_LIST_MAX_PAGES):
            result = await self._client._request(
                "GET",
                "/support/workspaces",
                params={
                    "limit": WORKSPACE_LIST_PAGE_SIZE,
                    "offset": page_number * WORKSPACE_LIST_PAGE_SIZE,
                },
                expected_response_shape="list_or_dict",
            )
            page = result if isinstance(result, list) else result.get("workspaces")
            if not isinstance(page, list):
                return result if isinstance(result, dict) else {"workspaces": workspaces}
            if page == previous:
                break
            previous = page
            fresh = [w for w in page if not isinstance(w, dict) or w.get("id") not in seen]
            seen.update(w["id"] for w in fresh if isinstance(w, dict) and "id" in w)
            workspaces.extend(fresh)
            if not fresh or len(page) < WORKSPACE_LIST_PAGE_SIZE:
                break
        return {"workspaces": workspaces}

    async def workspace_get(self, workspace_id: int, fields: str | None = None) -> dict[str, Any]:
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
        return await self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}", params=params or None
        )

    async def workspace_create(
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
        return await self._client._request_json("POST", "/support/workspaces", json=body)

    async def workspace_update(
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
        return await self._client._request_json(
            "PATCH", f"/support/workspaces/{workspace_id}", json=body
        )

    async def workspace_delete(self, workspace_id: int) -> dict[str, Any]:
        """Delete a workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with the deletion result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json("DELETE", f"/support/workspaces/{workspace_id}")

    async def workspace_suspend_access(
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
        return await self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/suspend-access", json=body
        )

    async def workspace_restore_access(self, workspace_id: int) -> dict[str, Any]:
        """Restore user access to a suspended workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with the restoration result.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/restore-access"
        )

    # -- Workspace users (support/admin) ------------------------------------------

    async def workspace_user_list(
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
        return await self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}/users", params=params or None
        )

    async def workspace_user_add(
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
        return await self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/users", json=body
        )

    async def workspace_user_remove(self, workspace_id: int, user_id: int) -> dict[str, Any]:
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
        return await self._client._request_json(
            "DELETE", f"/support/workspaces/{workspace_id}/users/{user_id}"
        )

    async def workspace_user_transfer(
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
        return await self._client._request_json(
            "PATCH", f"/support/workspaces/{workspace_id}/users", json=body
        )

    # -- Billing actions (per workspace) ------------------------------------------
    #
    # Money-moving admin actions on one workspace's subscription. Each needs a
    # super or tech admin and is recorded as an admin audit event. A
    # partner-billed workspace refuses the per-workspace actions; its recovery
    # runs through the ``partner_*`` methods.

    async def billing_start_trial(
        self, workspace_id: int, days: int | None = None
    ) -> dict[str, Any]:
        """Start a Pro trial on an existing workspace (no card needed).

        Replaces the workspace's billing with the trial. Refused for a live deal,
        a partner-billed, a Chargebee-billed or a deleted workspace.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            days: Trial length in days, 1 to 60. Omit for the Pro plan's own trial length.

        Returns:
            Dict with ``message`` and the started ``trial``.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer or
                *days* is outside 1 to 60.
        """
        _check_id("workspace_id", workspace_id)
        body: dict[str, Any] = {}
        if days is not None:
            if not _is_int(days) or not TRIAL_DAYS_MIN <= days <= TRIAL_DAYS_MAX:
                raise MammothValidationError(ERR_TRIAL_DAYS)
            body["days"] = days
        return await self._client._request_json(
            "POST", f"/support/billing/{workspace_id}/start-trial", json=body
        )

    async def billing_end_trial(self, workspace_id: int) -> dict[str, Any]:
        """End a workspace's trial and start billing.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with ``message``.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "POST", f"/support/billing/{workspace_id}/end-trial"
        )

    async def billing_retry_payment(self, workspace_id: int) -> dict[str, Any]:
        """Retry payment for a past-due workspace (charges its open invoices).

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with ``message`` and the payment service ``result``.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "POST", f"/support/billing/{workspace_id}/retry-payment"
        )

    async def billing_refund(
        self, workspace_id: int, amount: int | None = None, *, full: bool = False
    ) -> dict[str, Any]:
        """Refund a workspace's most recent payment, in full or in part.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            amount: Partial refund in cents (positive integer).
            full: ``True`` to refund the whole payment. Exactly one of *amount* and
                *full* is required, so a refund is never full by omission.

        Returns:
            Dict with ``message`` and the payment service ``result``.

        Raises:
            MammothValidationError: If *workspace_id* or *amount* is not a positive integer,
                or not exactly one of *amount* and *full* is given.
        """
        _check_id("workspace_id", workspace_id)
        if (amount is not None) == bool(full):
            raise MammothValidationError(ERR_REFUND_AMOUNT)
        params: dict[str, Any] | None = None
        if amount is not None:
            _check_id("amount", amount)
            params = {"amount": amount}
        return await self._client._request_json(
            "POST", f"/support/billing/{workspace_id}/refund", params=params
        )

    async def billing_change_plan(
        self,
        workspace_id: int,
        new_plan_id: int,
        *,
        when: str = "now",
        storage_gb: int | None = None,
    ) -> dict[str, Any]:
        """Change a workspace's self-serve plan.

        Refused for a live deal workspace (edit the deal instead), a partner-billed
        workspace, an archived workspace and a plan that is not current.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            new_plan_id: ID of the current catalog plan to move onto.
            when: ``"now"`` (prorated, the default) or ``"period_end"`` (at renewal).
            storage_gb: Total storage allocation on an inline-pricing target plan
                (its base size or one of its storage options).

        Returns:
            Dict with ``message`` (or ``message`` and ``chargebee`` for a Chargebee workspace).

        Raises:
            MammothValidationError: If an id is not a positive integer, *when* is
                not ``"now"`` or ``"period_end"``, or *storage_gb* is not positive.
        """
        _check_id("workspace_id", workspace_id)
        _check_id("new_plan_id", new_plan_id)
        if when not in BILLING_WHEN:
            raise MammothValidationError(ERR_BILLING_WHEN.format(value=when))
        body: dict[str, Any] = {"new_plan_id": new_plan_id, "when": when}
        if storage_gb is not None:
            _check_id("storage_gb", storage_gb)
            body["storage_gb"] = storage_gb
        return await self._client._request_json(
            "POST", f"/support/billing/{workspace_id}/change-plan", json=body
        )

    async def billing_cancel_subscription(self, workspace_id: int, when: str) -> dict[str, Any]:
        """Cancel a workspace's subscription (or its live deal).

        ``now`` stops billing today, turns the unused time into credit (no
        refund) and lands the workspace on Free. ``period_end`` keeps the plan
        until the paid period ends. A live deal is cancelled instead (a partner
        deal: ``now`` only).

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            when: ``"now"`` or ``"period_end"``.

        Returns:
            Dict with ``message``, ``when``, ``effective_at`` and ``deal_id``.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer or
                *when* is not ``"now"`` or ``"period_end"``.
        """
        _check_id("workspace_id", workspace_id)
        if when not in BILLING_WHEN:
            raise MammothValidationError(ERR_BILLING_WHEN.format(value=when))
        return await self._client._request_json(
            "POST", f"/support/billing/{workspace_id}/cancel-subscription", json={"when": when}
        )

    # -- Catalog reads -----------------------------------------------------------

    async def connector_bucket_impact(
        self, connector_id: int, bucket: str | None = None
    ) -> dict[str, Any]:
        """Read what moving a connector to another bucket does to access (read-only).

        Args:
            connector_id: ID of the connector (must be a positive integer).
            bucket: The bucket the connector would move to.

        Returns:
            Dict with ``connector``, ``from_bucket``, ``to_bucket``, ``levels``,
            ``change``, ``workspaces`` and ``connections``.

        Raises:
            MammothValidationError: If *connector_id* is not a positive integer.
        """
        _check_id("connector_id", connector_id)
        params = {"bucket": bucket} if bucket else None
        return await self._client._request_json(
            "GET", f"/support/connectors/{connector_id}/bucket-impact", params=params
        )

    async def entitlement_registry(self) -> dict[str, Any]:
        """Read the entitlement registry: what may be sold and what is never gated.

        Returns:
            Dict with ``registry`` and ``never_gated`` lists.
        """
        return await self._client._request_json("GET", "/support/entitlements")

    async def plan_catalog(self) -> dict[str, Any]:
        """Read the plan catalog: current, archived, legacy and system plans, ladder, matrix.

        Returns:
            Dict with ``current``, ``archived``, ``enterprise``, ``legacy``,
            ``system``, ``storage_steps``, ``matrix`` and related fields.
        """
        return await self._client._request_json("GET", "/support/plans/catalog")

    # -- Deals ------------------------------------------------------------------

    async def deal_list(self) -> dict[str, Any]:
        """List deals.

        Returns:
            Dict with the ``deals`` list.
        """
        return await self._client._request_json("GET", "/support/deals")

    async def deal_get(self, deal_id: int) -> dict[str, Any]:
        """Get one deal.

        Args:
            deal_id: ID of the deal (must be a positive integer).

        Returns:
            Dict with the ``deal``.

        Raises:
            MammothValidationError: If *deal_id* is not a positive integer.
        """
        _check_id("deal_id", deal_id)
        return await self._client._request_json("GET", f"/support/deals/{deal_id}")

    async def deal_create(
        self,
        base_plan_id: int,
        *,
        price: float | None = None,
        billing_interval: str | None = None,
        collection_method: str | None = None,
        currency: str | None = None,
        ent_overrides: dict[str, Any] | None = None,
        custom_connectors: list[str] | None = None,
        contract_start: str | None = None,
        contract_end: str | None = None,
        trial_end: str | None = None,
        payment_terms: str | None = None,
        notes: str | None = None,
        contact_name: str | None = None,
        contact_email: str | None = None,
        workspace_id: int | None = None,
        workspace_create: dict[str, Any] | None = None,
        customer_email: str | None = None,
        partner_id: int | None = None,
        billing_start: str | None = None,
        billing_start_at: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Create a deal: a base plan plus overrides, on one workspace.

        Give exactly one of *workspace_id* (an existing workspace) or
        *workspace_create* (a new workspace).

        Args:
            base_plan_id: ID of the plan the deal starts from (grants nothing without it).
            price: Price per billing interval.
            billing_interval: Billing cycle the server accepts (for example ``"monthly"``).
            collection_method: ``"charge_automatically"`` or ``"send_invoice"``.
            currency: Three-letter ISO currency code.
            ent_overrides: Entitlement registry keys the deal freezes, as ``{key: value}``.
            custom_connectors: Names of sources built for this account.
            contract_start: ISO 8601 timestamp.
            contract_end: ISO 8601 timestamp, after *contract_start*.
            trial_end: ISO 8601 timestamp; required when *status* is ``"trial"``.
            payment_terms: One of the fixed payment terms the server accepts.
            notes: Free-text notes.
            contact_name: Billing contact name (128 characters at most).
            contact_email: Billing contact email.
            workspace_id: Existing workspace to put on the deal.
            workspace_create: New workspace to create, as ``{"name": ..., "user_email": ...}``.
            customer_email: Customer email for the workspace's billing customer.
            partner_id: Partner that bills this deal.
            billing_start: ``"now"``, ``"chargebee_term_end"`` or ``"date"`` (a workspace
                leaving Chargebee); ``"date"`` needs *billing_start_at*.
            billing_start_at: ISO 8601 timestamp for ``billing_start="date"``.
            status: ``"active"`` (default) or ``"trial"``.

        Returns:
            Dict with the new deal ``id`` and its ``workspace_id``.

        Raises:
            MammothValidationError: If *base_plan_id* is not a positive integer or
                not exactly one of *workspace_id* / *workspace_create* is given.
        """
        _check_id("base_plan_id", base_plan_id)
        _check_interval(billing_interval)
        if bool(workspace_id) == bool(workspace_create):
            raise MammothValidationError(ERR_DEAL_WORKSPACE)
        body = _drop_none(
            base_plan_id=base_plan_id,
            price=price,
            billing_interval=billing_interval,
            collection_method=collection_method,
            currency=currency,
            ent_overrides=ent_overrides,
            custom_connectors=custom_connectors,
            contract_start=contract_start,
            contract_end=contract_end,
            trial_end=trial_end,
            payment_terms=payment_terms,
            notes=notes,
            contact_name=contact_name,
            contact_email=contact_email,
            workspace_id=workspace_id,
            workspace_create=workspace_create,
            customer_email=customer_email,
            partner_id=partner_id,
            billing_start=billing_start,
            billing_start_at=billing_start_at,
            status=status,
        )
        return await self._client._request_json("POST", "/support/deals", json=body)

    async def deal_update(
        self,
        deal_id: int,
        *,
        price: float | None = None,
        billing_interval: str | None = None,
        collection_method: str | None = None,
        currency: str | None = None,
        base_plan_id: int | None = None,
        ent_overrides: dict[str, Any] | None = None,
        custom_connectors: list[str] | None = None,
        contract_start: str | None = None,
        contract_end: str | None = None,
        trial_end: str | None = None,
        payment_terms: str | None = None,
        notes: str | None = None,
        contact_name: str | None = None,
        contact_email: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Update a deal's terms. Only the fields you pass change.

        The partner is not editable here: use ``deal_move_to_partner`` or
        ``partner_client_detach``.

        Args:
            deal_id: ID of the deal (must be a positive integer).
            price: Price per billing interval.
            billing_interval: Billing cycle the server accepts.
            collection_method: ``"charge_automatically"`` or ``"send_invoice"``.
            currency: Three-letter ISO currency code.
            base_plan_id: ID of the plan the deal starts from.
            ent_overrides: Entitlement registry keys the deal freezes, as ``{key: value}``.
            custom_connectors: Names of sources built for this account.
            contract_start: ISO 8601 timestamp.
            contract_end: ISO 8601 timestamp, after *contract_start*.
            trial_end: ISO 8601 timestamp.
            payment_terms: One of the fixed payment terms the server accepts.
            notes: Free-text notes.
            contact_name: Billing contact name (128 characters at most).
            contact_email: Billing contact email; an empty string clears it.
            status: New deal status (for example ``"active"``).

        Returns:
            Dict with the deal ``id`` and its ``workspace_id``.

        Raises:
            MammothValidationError: If *deal_id* is not a positive integer or no
                field to change is given.
        """
        _check_id("deal_id", deal_id)
        _check_interval(billing_interval)
        body = _drop_none(
            price=price,
            billing_interval=billing_interval,
            collection_method=collection_method,
            currency=currency,
            base_plan_id=base_plan_id,
            ent_overrides=ent_overrides,
            custom_connectors=custom_connectors,
            contract_start=contract_start,
            contract_end=contract_end,
            trial_end=trial_end,
            payment_terms=payment_terms,
            notes=notes,
            contact_name=contact_name,
            contact_email=contact_email,
            status=status,
        )
        if not body:
            raise MammothValidationError(ERR_DEAL_NO_CHANGE)
        return await self._client._request_json("PUT", f"/support/deals/{deal_id}", json=body)

    async def deal_activity(self, deal_id: int) -> dict[str, Any]:
        """Read a deal's activity feed (its events plus its workspace's billing events).

        Args:
            deal_id: ID of the deal (must be a positive integer).

        Returns:
            Dict with the ``activity`` rows.

        Raises:
            MammothValidationError: If *deal_id* is not a positive integer.
        """
        _check_id("deal_id", deal_id)
        return await self._client._request_json("GET", f"/support/deals/{deal_id}/activity")

    async def deal_preview_entitlement(self, deal_id: int) -> dict[str, Any]:
        """Preview a deal's resolved entitlement (base plan plus overrides).

        Args:
            deal_id: ID of the deal (must be a positive integer).

        Returns:
            Dict with the ``entitlement``.

        Raises:
            MammothValidationError: If *deal_id* is not a positive integer.
        """
        _check_id("deal_id", deal_id)
        return await self._client._request_json(
            "GET", f"/support/deals/{deal_id}/preview-entitlement"
        )

    async def deal_opt_in(
        self,
        deal_id: int,
        *,
        keys: list[str] | None = None,
        connectors: list[str] | None = None,
        everything: bool = False,
    ) -> dict[str, Any]:
        """Opt a deal in to catalog changes: release rollout pins so keys follow the base plan.

        Args:
            deal_id: ID of the deal (must be a positive integer).
            keys: Entitlement registry keys to release.
            connectors: Connector names to release.
            everything: Release every pin on the deal (sent as ``all``).

        Returns:
            Dict with the remaining ``pins``.

        Raises:
            MammothValidationError: If *deal_id* is not a positive integer or
                nothing to release is given.
        """
        _check_id("deal_id", deal_id)
        if not (keys or connectors or everything):
            raise MammothValidationError(ERR_DEAL_OPT_IN_EMPTY)
        body = {"keys": keys or [], "connectors": connectors or [], "all": everything}
        return await self._client._request_json(
            "POST", f"/support/deals/{deal_id}/opt-in", json=body
        )

    async def deal_move_to_partner(
        self,
        deal_id: int,
        partner_id: int,
        price: float,
        billing_interval: str,
        *,
        when: str = "period_end",
    ) -> dict[str, Any]:
        """Move a direct deal under a partner.

        Refused for a partner deal, an unpaid workspace, a pending detach or move,
        and a partner whose billing is stopped.

        Args:
            deal_id: ID of the deal (must be a positive integer).
            partner_id: ID of the partner to move under.
            price: The new price (usually the partner's wholesale price), 0 or more.
            billing_interval: Billing cycle the server accepts.
            when: ``"period_end"`` (default, no proration) or ``"now"`` (cancels the
                workspace's subscription prorated and refunds the unused time).

        Returns:
            Dict with the scheduled ``move``.

        Raises:
            MammothValidationError: If an id is not a positive integer, *price* is
                negative or *when* is not ``"period_end"`` or ``"now"``.
        """
        _check_id("deal_id", deal_id)
        _check_id("partner_id", partner_id)
        if not _is_number(price) or price < 0:
            raise MammothValidationError(ERR_PRICE_NEGATIVE)
        _check_interval(billing_interval)
        if when not in MOVE_WHEN:
            raise MammothValidationError(ERR_MOVE_WHEN.format(value=when))
        body = {
            "partner_id": partner_id,
            "price": price,
            "billing_interval": billing_interval,
            "when": when,
        }
        return await self._client._request_json(
            "POST", f"/support/deals/{deal_id}/move-to-partner", json=body
        )

    async def deal_cancel_move_to_partner(self, deal_id: int) -> dict[str, Any]:
        """Cancel a scheduled move of a deal under a partner.

        Args:
            deal_id: ID of the deal (must be a positive integer).

        Returns:
            Dict with ``message``.

        Raises:
            MammothValidationError: If *deal_id* is not a positive integer.
        """
        _check_id("deal_id", deal_id)
        return await self._client._request_json(
            "DELETE", f"/support/deals/{deal_id}/move-to-partner"
        )

    # -- Identities (cross-tenant users) ----------------------------------------

    async def identity_list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
        sort: str | None = None,
        order: str | None = None,
    ) -> dict[str, Any]:
        """List users identity-first, each with workspace counts.

        Args:
            limit: Page size used for each request, 1 to 100 (default 100). All pages
                are read; this does not cap the result.
            offset: Row to start from.
            search: Filter by email or name.
            sort: ``name``, ``email`` or ``last_active``.
            order: ``asc`` or ``desc``.

        Returns:
            Dict with every matching user under ``users``; the pages are followed to the
            end (a repeated page stops the loop).
        """
        size = min(limit, IDENTITY_LIST_PAGE_SIZE) if limit else IDENTITY_LIST_PAGE_SIZE
        start = offset or 0
        users: list[Any] = []
        seen: set[Any] = set()
        previous: list[Any] | None = None
        for page_number in range(IDENTITY_LIST_MAX_PAGES):
            params = _drop_none(
                limit=size, offset=start + page_number * size, search=search, sort=sort, order=order
            )
            result = await self._client._request_json("GET", "/support/identities", params=params)
            page = result.get("users")
            if not isinstance(page, list):
                return result
            if page == previous:
                break
            previous = page
            fresh = [u for u in page if not isinstance(u, dict) or u.get("id") not in seen]
            seen.update(u["id"] for u in fresh if isinstance(u, dict) and "id" in u)
            users.extend(fresh)
            if not fresh or len(page) < size:
                break
        return {"users": users}

    async def identity_get(self, user_id: int) -> dict[str, Any]:
        """Get one user's identity: workspace memberships and roles.

        Args:
            user_id: ID of the user (must be a positive integer).

        Returns:
            Dict with the ``user``.

        Raises:
            MammothValidationError: If *user_id* is not a positive integer.
        """
        _check_id("user_id", user_id)
        return await self._client._request_json("GET", f"/support/identities/{user_id}")

    # -- Partners ---------------------------------------------------------------

    async def partner_list(self) -> dict[str, Any]:
        """List partners.

        Returns:
            Dict with the ``partners`` list.
        """
        return await self._client._request_json("GET", "/support/partners")

    async def partner_get(self, partner_id: int) -> dict[str, Any]:
        """Get one partner.

        Args:
            partner_id: ID of the partner (must be a positive integer).

        Returns:
            Dict with the ``partner``.

        Raises:
            MammothValidationError: If *partner_id* is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        return await self._client._request_json("GET", f"/support/partners/{partner_id}")

    async def partner_create(
        self,
        name: str,
        *,
        contact_name: str | None = None,
        contact_email: str | None = None,
        payment_terms: str | None = None,
        billing_method: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a partner.

        Args:
            name: Partner name.
            contact_name: Billing contact name.
            contact_email: Billing contact email (Stripe customer and payment-link emails).
            payment_terms: Payment terms the server accepts.
            billing_method: ``"send_invoice"`` (default) or ``"charge_automatically"``; the
                collection method of the partner's consolidated subscription.
            notes: Free-text notes.

        Returns:
            Dict with the new partner ``id`` and ``name``.
        """
        body = _drop_none(
            name=name,
            contact_name=contact_name,
            contact_email=contact_email,
            payment_terms=payment_terms,
            billing_method=billing_method,
            notes=notes,
        )
        return await self._client._request_json("POST", "/support/partners", json=body)

    async def partner_update(
        self,
        partner_id: int,
        *,
        name: str | None = None,
        contact_name: str | None = None,
        contact_email: str | None = None,
        payment_terms: str | None = None,
        billing_method: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update a partner. Only the fields you pass change.

        An empty string for *contact_name*, *contact_email* or *notes* clears it.

        Args:
            partner_id: ID of the partner (must be a positive integer).
            name: New partner name.
            contact_name: Billing contact name.
            contact_email: Billing contact email.
            payment_terms: Payment terms the server accepts.
            billing_method: ``"send_invoice"`` or ``"charge_automatically"``.
            status: New partner status.
            notes: Free-text notes.

        Returns:
            Dict with the partner ``id`` and ``name``.

        Raises:
            MammothValidationError: If *partner_id* is not a positive integer or no
                field to change is given.
        """
        _check_id("partner_id", partner_id)
        body = _drop_none(
            name=name,
            contact_name=contact_name,
            contact_email=contact_email,
            payment_terms=payment_terms,
            billing_method=billing_method,
            status=status,
            notes=notes,
        )
        if not body:
            raise MammothValidationError(ERR_PARTNER_NO_CHANGE)
        return await self._client._request_json("PUT", f"/support/partners/{partner_id}", json=body)

    async def partner_activity(self, partner_id: int) -> dict[str, Any]:
        """Read a partner's admin activity feed.

        Args:
            partner_id: ID of the partner (must be a positive integer).

        Returns:
            Dict with the ``activity`` rows.

        Raises:
            MammothValidationError: If *partner_id* is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        return await self._client._request_json("GET", f"/support/partners/{partner_id}/activity")

    async def partner_billing(self, partner_id: int) -> dict[str, Any]:
        """Read a partner's consolidated billing: the total and the per-client lines.

        Args:
            partner_id: ID of the partner (must be a positive integer).

        Returns:
            Dict with the ``billing`` breakdown.

        Raises:
            MammothValidationError: If *partner_id* is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        return await self._client._request_json("GET", f"/support/partners/{partner_id}/billing")

    async def partner_invoices(self, partner_id: int) -> dict[str, Any]:
        """List a partner's consolidated Stripe invoices.

        Args:
            partner_id: ID of the partner (must be a positive integer).

        Returns:
            Dict with the ``invoices`` list.

        Raises:
            MammothValidationError: If *partner_id* is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        return await self._client._request_json("GET", f"/support/partners/{partner_id}/invoices")

    async def partner_charge_invoices(self, partner_id: int) -> dict[str, Any]:
        """Charge a partner's open invoices (recovers an incomplete subscription).

        Args:
            partner_id: ID of the partner (must be a positive integer).

        Returns:
            Dict with the per-invoice ``result``.

        Raises:
            MammothValidationError: If *partner_id* is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        return await self._client._request_json(
            "POST", f"/support/partners/{partner_id}/charge-invoices"
        )

    async def partner_send_payment_link(self, partner_id: int) -> dict[str, Any]:
        """Email the partner a link to add or update their payment method.

        Args:
            partner_id: ID of the partner (must be a positive integer).

        Returns:
            Dict with ``message`` naming the address the link went to.

        Raises:
            MammothValidationError: If *partner_id* is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        return await self._client._request_json(
            "POST", f"/support/partners/{partner_id}/send-payment-link"
        )

    async def partner_client_list(self, partner_id: int) -> dict[str, Any]:
        """List a partner's client workspaces.

        Args:
            partner_id: ID of the partner (must be a positive integer).

        Returns:
            Dict with the ``clients`` list.

        Raises:
            MammothValidationError: If *partner_id* is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        return await self._client._request_json("GET", f"/support/partners/{partner_id}/workspaces")

    async def partner_client_delete(self, partner_id: int, workspace_id: int) -> dict[str, Any]:
        """Delete a partner's client workspace and remove its prorated line item.

        Args:
            partner_id: ID of the partner that bills the workspace.
            workspace_id: ID of the client workspace to delete.

        Returns:
            Dict with ``message``.

        Raises:
            MammothValidationError: If an id is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "DELETE", f"/support/partners/{partner_id}/workspaces/{workspace_id}"
        )

    async def partner_client_detach(
        self,
        partner_id: int,
        workspace_id: int,
        price: float,
        contact_email: str,
        *,
        billing_interval: str | None = None,
        collection_method: str | None = None,
        currency: str | None = None,
        base_plan_id: int | None = None,
        ent_overrides: dict[str, Any] | None = None,
        custom_connectors: list[str] | None = None,
        contract_start: str | None = None,
        contract_end: str | None = None,
        trial_end: str | None = None,
        payment_terms: str | None = None,
        notes: str | None = None,
        contact_name: str | None = None,
    ) -> dict[str, Any]:
        """Detach a partner's client workspace to direct billing.

        Schedules the cutover at the partner's period end with the direct deal's
        new terms. When the partner's billing has stopped, it runs now and restores
        the client's access. Refused for a cancelled deal.

        Args:
            partner_id: ID of the partner that bills the workspace.
            workspace_id: ID of the client workspace.
            price: What the customer pays Mammoth directly (not the wholesale price), above 0.
            contact_email: Billing email of the workspace's Stripe customer.
            billing_interval: Billing cycle the server accepts.
            collection_method: ``"charge_automatically"`` or ``"send_invoice"``.
            currency: Three-letter ISO currency code.
            base_plan_id: ID of the plan the direct deal starts from.
            ent_overrides: Entitlement registry keys the deal freezes, as ``{key: value}``.
            custom_connectors: Names of sources built for this account.
            contract_start: ISO 8601 timestamp.
            contract_end: ISO 8601 timestamp, after *contract_start*.
            trial_end: ISO 8601 timestamp.
            payment_terms: One of the fixed payment terms the server accepts.
            notes: Free-text notes.
            contact_name: Billing contact name (128 characters at most).

        Returns:
            Dict with the pending ``detach`` (``None`` when it ran now) and ``message``.

        Raises:
            MammothValidationError: If an id is not a positive integer or *price* is not above 0.
        """
        _check_id("partner_id", partner_id)
        _check_id("workspace_id", workspace_id)
        if not _is_number(price) or price <= 0:
            raise MammothValidationError(ERR_PRICE_POSITIVE)
        _check_interval(billing_interval)
        body = _drop_none(
            price=price,
            contact_email=contact_email,
            billing_interval=billing_interval,
            collection_method=collection_method,
            currency=currency,
            base_plan_id=base_plan_id,
            ent_overrides=ent_overrides,
            custom_connectors=custom_connectors,
            contract_start=contract_start,
            contract_end=contract_end,
            trial_end=trial_end,
            payment_terms=payment_terms,
            notes=notes,
            contact_name=contact_name,
        )
        return await self._client._request_json(
            "POST", f"/support/partners/{partner_id}/workspaces/{workspace_id}/detach", json=body
        )

    async def partner_client_cancel_detach(
        self, partner_id: int, workspace_id: int
    ) -> dict[str, Any]:
        """Cancel a scheduled detach of a client workspace to direct billing.

        Args:
            partner_id: ID of the partner that bills the workspace.
            workspace_id: ID of the client workspace.

        Returns:
            Dict with ``message``.

        Raises:
            MammothValidationError: If an id is not a positive integer.
        """
        _check_id("partner_id", partner_id)
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "DELETE", f"/support/partners/{partner_id}/workspaces/{workspace_id}/detach"
        )

    # -- Admin home --------------------------------------------------------------

    async def search(self, q: str = "") -> dict[str, Any]:
        """Search workspaces, partners and users at once.

        Args:
            q: Search text.

        Returns:
            Dict with the matching ``results``.
        """
        return await self._client._request_json("GET", "/support/search", params={"q": q})

    async def triage(self) -> dict[str, Any]:
        """List the admin triage ("needs you") items.

        Returns:
            Dict with the ``items`` list.
        """
        return await self._client._request_json("GET", "/support/triage")

    async def usage_tiles(self) -> dict[str, Any]:
        """Read the admin home headline counts.

        Returns:
            Dict with the ``tiles``.
        """
        return await self._client._request_json("GET", "/support/usage-tiles")

    # -- Workspace admin (activity, entitlement, archive) ------------------------

    async def workspace_activity(self, workspace_id: int) -> dict[str, Any]:
        """Read a workspace's admin activity feed (including its deal's billing events).

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with the ``activity`` rows.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}/activity"
        )

    async def workspace_entitlement(self, workspace_id: int) -> dict[str, Any]:
        """Read a workspace's resolved entitlement, current usage and billing source.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with ``entitlement``, ``usage`` and ``billing``.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}/entitlement"
        )

    async def workspace_deal_seed(self, workspace_id: int) -> dict[str, Any]:
        """Read the deal terms seeded from a workspace's live subscription ("Convert to deal").

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with ``seed``, ``chargebee``, ``current`` and ``usage``.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}/deal-seed"
        )

    async def workspace_chargebee_cancelled(self, workspace_id: int) -> dict[str, Any]:
        """Confirm that the old Chargebee subscription was cancelled in Chargebee.

        The checklist step after a Chargebee-to-Stripe deal conversion. The API
        never writes to Chargebee; this only records the admin's confirmation.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with the ``chargebee`` record.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/chargebee-cancelled"
        )

    async def workspace_archive_info(self, workspace_id: int) -> dict[str, Any]:
        """Read whether a workspace may be archived now, and the archive progress.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with ``eligible``, ``block_code``, ``block_reason``, ``billing_to_end``,
            ``estimate_bytes``, the storage classes and the archive ledger.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "GET", f"/support/workspaces/{workspace_id}/archive"
        )

    async def workspace_archive(
        self,
        workspace_id: int,
        storage_class: str,
        confirm_name: str,
        *,
        reason: str | None = None,
        cancel_billing: bool = False,
    ) -> dict[str, Any]:
        """Archive a workspace to cold storage, or retry a failed archive.

        Blocks the workspace (status ARCHIVED) and queues the job that moves its
        data to S3. Live billing (deal, Stripe subscription, add-ons) is cancelled
        first, now and with no refund, only when *cancel_billing* is true.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            storage_class: S3 storage class: ``"GLACIER_IR"`` or ``"DEEP_ARCHIVE"``. A retry
                keeps the class it started with.
            confirm_name: The workspace name, typed to confirm (case-sensitive).
            reason: Reason recorded with the archive.
            cancel_billing: Confirm that archiving cancels live billing now, with no refund.

        Returns:
            Dict with the archive ``ledger``.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer,
                *storage_class* is unknown or *confirm_name* is empty.
        """
        _check_id("workspace_id", workspace_id)
        if storage_class not in ARCHIVE_STORAGE_CLASSES:
            raise MammothValidationError(ERR_STORAGE_CLASS.format(value=storage_class))
        if not confirm_name:
            raise MammothValidationError(ERR_CONFIRM_NAME)
        body: dict[str, Any] = {
            "storage_class": storage_class,
            "confirm_name": confirm_name,
            "cancel_billing": cancel_billing,
        }
        if reason is not None:
            body["reason"] = reason
        return await self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/archive", json=body
        )

    async def workspace_restore_archive(self, workspace_id: int) -> dict[str, Any]:
        """Restore an archived workspace from cold storage, or retry a failed restore.

        The workspace stays ARCHIVED until the restore job finishes.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).

        Returns:
            Dict with the archive ``ledger``.

        Raises:
            MammothValidationError: If *workspace_id* is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        return await self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/restore"
        )

    async def workspace_invite_cancel(self, workspace_id: int, invite_id: int) -> dict[str, Any]:
        """Cancel a pending workspace invite.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            invite_id: ID of the pending invite.

        Returns:
            Dict with ``message`` naming the invited address.

        Raises:
            MammothValidationError: If an id is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        _check_id("invite_id", invite_id)
        return await self._client._request_json(
            "DELETE", f"/support/workspaces/{workspace_id}/users/invites/{invite_id}"
        )

    async def workspace_invite_resend(self, workspace_id: int, invite_id: int) -> dict[str, Any]:
        """Resend a pending workspace invite.

        Args:
            workspace_id: ID of the target workspace (must be a positive integer).
            invite_id: ID of the pending invite.

        Returns:
            Dict with ``message`` naming the invited address.

        Raises:
            MammothValidationError: If an id is not a positive integer.
        """
        _check_id("workspace_id", workspace_id)
        _check_id("invite_id", invite_id)
        return await self._client._request_json(
            "POST", f"/support/workspaces/{workspace_id}/users/invites/{invite_id}/resend"
        )

    # -- Curated template catalog (dashboards v3 admin) ---------------------------
    #
    # Every route below refuses a caller without a Mammoth staff (platform-admin)
    # role, whatever workspace the session is in. They act on CURATED templates
    # only; a workspace's saved templates are never reachable here.

    async def template_list(self) -> dict[str, Any]:
        """List every curated template, drafts and broken rows included, worst first.

        Returns:
            Dict with ``templates`` (each with its state, what is wrong and the
            action that fixes it), ``counts`` and the filing vocabularies.
        """
        return await self._client._request_json("GET", _TEMPLATE_ADMIN)

    async def template_edit(self, slug: str, changes: dict[str, Any]) -> dict[str, Any]:
        """Edit a curated template's filing: title, description, tags or order.

        Args:
            slug: Template slug.
            changes: Fields to change, from ``title``, ``description``,
                ``use_case``, ``function``, ``industry`` (list) and
                ``sort_order``; an explicit ``None`` clears a field. An optional
                ``base_version`` (the row's ``filing_version``) makes the write
                conditional (409 when the row moved).

        Returns:
            Dict with ``template`` and ``notes`` (what the edit changes for
            customers).

        Raises:
            MammothValidationError: If *slug* or *changes* is empty.
        """
        path = _template_path(slug)
        if not changes:
            raise MammothValidationError(ERR_TEMPLATE_CHANGES_EMPTY)
        return await self._client._request_json("PATCH", path, json={"params": dict(changes)})

    async def template_data_preview(self, slug: str) -> dict[str, Any]:
        """Read up to 50 rows of the data a curated template opens on.

        Args:
            slug: Template slug.

        Returns:
            Dict with the columns, rows and ``capped``.
        """
        return await self._client._request_json("GET", _template_path(slug, "/data-preview"))

    async def template_canvas(self, slug: str) -> dict[str, Any]:
        """Read a curated template's canvas, drafts included (as the editor reads it).

        Args:
            slug: Template slug.

        Returns:
            Dict with the canvas and its baked plan and specs.
        """
        return await self._client._request_json("GET", _template_path(slug, "/canvas"))

    async def template_publish(self, slug: str) -> dict[str, Any]:
        """Take a curated draft live in the gallery for every customer.

        Re-checks the fit, publishes the source dashboard and renders the
        preview image first; refused with nothing published when the template
        fails on its own data.

        Args:
            slug: Template slug.

        Returns:
            Dict with ``template``.
        """
        return await self._client._request_json("POST", _template_path(slug, "/publish"))

    async def template_unpublish(self, slug: str) -> dict[str, Any]:
        """Take a live (or retired) curated template back to draft.

        Args:
            slug: Template slug.

        Returns:
            Dict with ``template``.
        """
        return await self._client._request_json("POST", _template_path(slug, "/unpublish"))

    async def template_retire(self, slug: str) -> dict[str, Any]:
        """Retire a curated template: kept, no longer offered or audited.

        Reversible with :meth:`template_unpublish`.

        Args:
            slug: Template slug.

        Returns:
            Dict with ``template``.
        """
        return await self._client._request_json("POST", _template_path(slug, "/retire"))

    async def template_inspect(self, file: str | Path) -> dict[str, Any]:
        """Read a template file (.zip bundle) without importing it. Writes nothing.

        Args:
            file: Path to a local template bundle.

        Returns:
            Dict with the slug, the fields it needs, whether it carries data
            and a picture, and whether the catalog already has it.

        Raises:
            MammothValidationError: If *file* is not a local file.
        """
        path = _local_file(file)
        with path.open("rb") as opened:
            return await self._client._request_json(
                "POST",
                f"{_TEMPLATE_ADMIN}/inspect",
                files=[("data", (path.name, opened, "application/zip"))],
            )

    async def template_import(self, file: str | Path, dataset: str | None = None) -> dict[str, Any]:
        """Import a template file as a curated DRAFT (not published).

        Re-importing an existing slug updates it in place and keeps its filing.

        Args:
            file: Path to a local template bundle.
            dataset: Dataset name to bind a bundle that carries no data.

        Returns:
            Dict with the row, ``created`` and how every column was read.

        Raises:
            MammothValidationError: If *file* is not a local file.
        """
        path = _local_file(file)
        with path.open("rb") as opened:
            return await self._client._request_json(
                "POST",
                f"{_TEMPLATE_ADMIN}/import",
                params={"dataset": dataset} if dataset else None,
                files=[("data", (path.name, opened, "application/zip"))],
            )

    async def template_thumbnail_set(self, slug: str, file: str | Path) -> dict[str, Any]:
        """Upload or replace a curated template's picture (PNG, JPEG or WebP, 1 MB).

        Args:
            slug: Template slug.
            file: Path to a local image.

        Returns:
            Dict with ``template``.

        Raises:
            MammothValidationError: If *slug* is empty or *file* is not a local file.
        """
        endpoint = _template_path(slug, "/thumbnail")
        path = _local_file(file)
        with path.open("rb") as opened:
            return await self._client._request_json(
                "PUT",
                endpoint,
                files=[("data", (path.name, opened, "application/octet-stream"))],
            )

    async def template_thumbnail_clear(self, slug: str) -> dict[str, Any]:
        """Remove a curated template's picture; its card falls back to the og-card.

        Args:
            slug: Template slug.

        Returns:
            Dict with ``template``.
        """
        return await self._client._request_json("DELETE", _template_path(slug, "/thumbnail"))

    async def template_discard(self, slug: str) -> dict[str, Any]:
        """Permanently remove a curated DRAFT, its preview board and its data.

        Refused for a live template (unpublish it first). Boards people built
        from it are their own copies and keep working.

        Args:
            slug: Template slug.

        Returns:
            Dict with ``deleted`` and ``notes``.
        """
        return await self._client._request_json("DELETE", _template_path(slug))

    async def template_snapshots(self) -> dict[str, Any]:
        """List every stored dataset the template catalog holds.

        Returns:
            Dict with ``snapshots`` (size, content address, templates sharing
            it) and ``unstored`` (templates with no data).
        """
        return await self._client._request_json("GET", f"{_TEMPLATE_ADMIN}/snapshots")

    async def template_audit(self) -> dict[str, Any]:
        """Re-run every curated-catalog gate. Read-only; safe on a schedule.

        Returns:
            Dict with ``faults`` (each with its remedy), ``checked`` and
            ``missing``.
        """
        return await self._client._request_json("GET", f"{_TEMPLATE_ADMIN}/audit")

    async def template_export(
        self, slug: str, output_path: str | Path | None = None, with_data: bool = False
    ) -> Path:
        """Download a curated template as a template file (.zip) to a local path.

        Args:
            slug: Template slug.
            output_path: Where to write it (default ``<slug>.zip``).
            with_data: Also package a capped copy of the rows it opens on.

        Returns:
            Path of the written file.
        """
        artifact = await self._client._request_binary(
            "GET", _template_path(slug, "/export"), params={"data": "1" if with_data else "0"}
        )
        return await asyncio.to_thread(_save_zip, artifact, output_path or f"{slug}.zip")

    async def template_export_dashboard(
        self,
        dashboard_id: int,
        slug: str,
        output_path: str | Path | None = None,
        with_data: bool = True,
    ) -> Path:
        """Download any dashboard you can edit as a template file (.zip).

        Args:
            dashboard_id: ID of the dashboard (must be a positive integer).
            slug: Template id the file carries; an import matches on it.
            output_path: Where to write it (default ``<slug>.zip``).
            with_data: Package a capped copy of the board's rows (default on).

        Returns:
            Path of the written file.

        Raises:
            MammothValidationError: If *dashboard_id* is not a positive integer
                or *slug* is empty.
        """
        _check_id("dashboard_id", dashboard_id)
        if not slug:
            raise MammothValidationError(ERR_SLUG_EMPTY)
        artifact = await self._client._request_binary(
            "GET",
            f"{_TEMPLATE_ADMIN}/dashboards/{dashboard_id}/export",
            params={"slug": slug, "data": "1" if with_data else "0"},
        )
        return await asyncio.to_thread(_save_zip, artifact, output_path or f"{slug}.zip")


def _save_zip(artifact: dict[str, Any], output_path: str | Path) -> Path:
    """Write a downloaded template file to disk, atomically."""
    try:
        content = base64.b64decode(artifact["content_base64"])
    except (KeyError, ValueError) as exc:
        raise MammothValidationError("Invalid template export response.") from exc
    return _write_bytes_atomic(content, Path(output_path))
