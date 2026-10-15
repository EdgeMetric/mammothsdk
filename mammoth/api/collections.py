"""Collections API client: a named, ordered set of dashboards shared as one thing."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias: CollectionsAPI.list shadows the builtin in later annotations.

ERR_ID_POSITIVE = "`{0}` must be a positive integer, got {1!r}."
ERR_NAME = "`name` must be 1 to 120 characters."
ERR_DASHBOARD_IDS_EMPTY = "`dashboard_ids` must be a non-empty list of dashboard ids."
ERR_EMAILS = "`emails` must be 1 to 200 email addresses."
ERR_EMAIL_EMPTY = "`email` must be a non-empty string."
ERR_URL_EMPTY = "`url` must be a non-empty string."
ERR_FILES_EMPTY = "`files` must be a non-empty list of local file paths."
ERR_FILE_MISSING = "File not found: {0}"
ERR_UPDATE_EMPTY = "Give at least one field to change."
ERR_TRIGGER = "`trigger` must be one of new_data, schedule, got {0!r}."
ERR_FREQUENCY = "`frequency` must be one of daily, weekdays, weekly, monthly, got {0!r}."
ERR_WEEKDAY = "`weekday` must be 0 (Monday) to 6 (Sunday), got {0!r}."
ERR_MONTHDAY = "`monthday` must be 1 to 28, got {0!r}."
ERR_TIME_OF_DAY = "`time_of_day` must be HH:MM (24-hour), got {0!r}."
ERR_TIMEZONE = "`timezone` must be an IANA time zone name of 1 to 64 characters."
ERR_NUMBERS = "`numbers` must map a dashboard id to a list of figure keys."
ERR_SUBSCRIBED = "`subscribed` must be true or false."
_EMAIL_TRIGGERS = ("new_data", "schedule")
_EMAIL_FREQUENCIES = ("daily", "weekdays", "weekly", "monthly")
_TIME_OF_DAY = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_SHARE_MAX_EMAILS = 200
_NAME_MAX = 120


def _require_id(name: str, value: int) -> None:
    """Reject an id that is not a positive integer."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise MammothValidationError(ERR_ID_POSITIVE.format(name, value))


def _email_update_body(
    enabled: bool,
    timezone: str,
    trigger: str | None,
    frequency: str | None,
    weekday: int | None,
    monthday: int | None,
    time_of_day: str | None,
    numbers: dict[str, _list[str]] | None,
) -> dict[str, Any]:
    """Validate the email-update settings and build the request body (None fields left out)."""
    if not isinstance(enabled, bool):
        raise MammothValidationError("`enabled` must be true or false.")
    if not isinstance(timezone, str) or not 1 <= len(timezone) <= 64:
        raise MammothValidationError(ERR_TIMEZONE)
    if trigger is not None and trigger not in _EMAIL_TRIGGERS:
        raise MammothValidationError(ERR_TRIGGER.format(trigger))
    if frequency is not None and frequency not in _EMAIL_FREQUENCIES:
        raise MammothValidationError(ERR_FREQUENCY.format(frequency))
    if weekday is not None and (isinstance(weekday, bool) or weekday not in range(7)):
        raise MammothValidationError(ERR_WEEKDAY.format(weekday))
    if monthday is not None and (isinstance(monthday, bool) or monthday not in range(1, 29)):
        raise MammothValidationError(ERR_MONTHDAY.format(monthday))
    if time_of_day is not None and not (
        isinstance(time_of_day, str) and _TIME_OF_DAY.match(time_of_day)
    ):
        raise MammothValidationError(ERR_TIME_OF_DAY.format(time_of_day))
    if numbers is not None and not (
        isinstance(numbers, dict)
        and all(
            isinstance(key, str)
            and isinstance(keys, list)
            and all(isinstance(k, str) for k in keys)
            for key, keys in numbers.items()
        )
    ):
        raise MammothValidationError(ERR_NUMBERS)
    body: dict[str, Any] = {"enabled": enabled, "timezone": timezone}
    optional = {
        "trigger": trigger,
        "frequency": frequency,
        "weekday": weekday,
        "monthday": monthday,
        "time_of_day": time_of_day,
        "numbers": numbers,
    }
    body.update({key: value for key, value in optional.items() if value is not None})
    return body


class CollectionsAPI:
    """Client for collections: named sets of dashboards shared as one thing.

    Access via ``client.collections``::

        created = await client.collections.create("Q3 pack", project_id=7, dashboard_ids=[331])
        await client.collections.share(created["id"], ["ana@example.com"])
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _proj(self, project_id: int | None = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, "project_id", None)
        if proj is not None:
            return int(proj)
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    async def list(self) -> dict[str, Any]:
        """List the collections the caller manages or was shared.

        Returns:
            Dict ``{"collections": [...]}``; each summary has ``id``, ``name``, ``url``,
            ``project_id``, ``role`` (``manager`` or ``member``), ``dashboard_count`` and
            ``member_count`` (managers only).
        """
        headers = {"x-workspace-id": str(self._client.workspace_id)}
        return await self._client._request_json("GET", "/collections", headers=headers)

    async def get(self, collection_id: int) -> dict[str, Any]:
        """Get one collection with its dashboards, members and refresh setup.

        Args:
            collection_id: ID of the collection (must be > 0).

        Returns:
            Dict with the summary fields plus ``dashboards``, ``members`` (managers only),
            ``automation_id``, ``refresh_folder_resource_id`` and ``refresh_datasets``.

        Raises:
            MammothValidationError: If *collection_id* ≤ 0.
        """
        _require_id("collection_id", collection_id)
        return await self._client._request_json("GET", f"/collections/{collection_id}")

    async def get_by_url(
        self, url: str, t: str | None = None, email: str | None = None
    ) -> dict[str, Any]:
        """Open a collection by its share link, as a viewer does.

        Args:
            url: The collection's ``url`` token.
            t: Invite token, redeemed on the way in.
            email: Email the invite was sent to.

        Returns:
            The collection, as ``get`` returns it.

        Raises:
            MammothValidationError: If *url* is empty.
        """
        if not isinstance(url, str) or not url:
            raise MammothValidationError(ERR_URL_EMPTY)
        params = {k: v for k, v in (("t", t), ("email", email)) if v}
        return await self._client._request_json(
            "GET", f"/collections/url/{quote(url, safe='')}", params=params or None
        )

    async def create(
        self,
        name: str,
        project_id: int | None = None,
        description: str | None = None,
        dashboard_ids: _list[int] | None = None,
    ) -> dict[str, Any]:
        """Create a collection in a project.

        Args:
            name: Name, 1 to 120 characters.
            project_id: Project the collection belongs to; defaults to the client's project.
            description: Optional text, at most 2000 characters.
            dashboard_ids: Dashboards to put in it, in order.

        Returns:
            The new collection, as ``get`` returns it.

        Raises:
            MammothValidationError: If *name* is empty or over 120 characters, or an id ≤ 0.
        """
        if not isinstance(name, str) or not 1 <= len(name) <= _NAME_MAX:
            raise MammothValidationError(ERR_NAME)
        project_id = self._proj(project_id)
        _require_id("project_id", project_id)
        ids = [] if dashboard_ids is None else dashboard_ids
        for dashboard_id in ids:
            _require_id("dashboard_ids", dashboard_id)
        return await self._client._request_json(
            "POST",
            "/collections",
            json={
                "project_id": project_id,
                "name": name,
                "description": description,
                "dashboard_ids": ids,
            },
        )

    async def update(
        self,
        collection_id: int,
        name: str | None = None,
        description: str | None = None,
        order: _list[int] | None = None,
        tab_labels: dict[str, str | None] | None = None,
        automation_id: int | None = None,
        unlink_automation: bool = False,
    ) -> dict[str, Any]:
        """Rename, reorder, relabel or link the refresh automation of a collection.

        Only the fields given are sent.

        Args:
            collection_id: ID of the collection (must be > 0).
            name: New name, 1 to 120 characters.
            description: New description.
            order: Every dashboard id of the collection, in the new order.
            tab_labels: Dashboard id (as a string) to a short tab label; empty clears it.
            automation_id: Link this automation for upload-to-refresh.
            unlink_automation: Remove the linked automation.

        Returns:
            The updated collection, as ``get`` returns it.

        Raises:
            MammothValidationError: If nothing is given, an id ≤ 0 or *name* is invalid.
        """
        _require_id("collection_id", collection_id)
        body: dict[str, Any] = {
            key: value
            for key, value in (
                ("name", name),
                ("description", description),
                ("order", order),
                ("tab_labels", tab_labels),
                ("automation_id", automation_id),
            )
            if value is not None
        }
        if unlink_automation:
            body["unlink_automation"] = True
        if not body:
            raise MammothValidationError(ERR_UPDATE_EMPTY)
        if name is not None and not 1 <= len(name) <= _NAME_MAX:
            raise MammothValidationError(ERR_NAME)
        for dashboard_id in order or []:
            _require_id("order", dashboard_id)
        if automation_id is not None:
            _require_id("automation_id", automation_id)
        return await self._client._request_json("PATCH", f"/collections/{collection_id}", json=body)

    async def delete(self, collection_id: int) -> dict[str, Any]:
        """Delete a collection. Its dashboards are kept.

        Args:
            collection_id: ID of the collection (must be > 0).

        Returns:
            ``{"collection_id": ..., "deleted": True}``.

        Raises:
            MammothValidationError: If *collection_id* ≤ 0.
        """
        _require_id("collection_id", collection_id)
        await self._client._request_json("DELETE", f"/collections/{collection_id}")
        return {"collection_id": collection_id, "deleted": True}

    async def add_dashboards(
        self, collection_id: int, dashboard_ids: _list[int], notify: bool = False
    ) -> dict[str, Any]:
        """Add dashboards to a collection.

        Args:
            collection_id: ID of the collection (must be > 0).
            dashboard_ids: Dashboards to add (at least one).
            notify: Email the collection's members about them.

        Returns:
            Dict with ``added`` (dashboard ids) and ``notified`` (people emailed).

        Raises:
            MammothValidationError: If *dashboard_ids* is empty or an id ≤ 0.
        """
        _require_id("collection_id", collection_id)
        if not dashboard_ids:
            raise MammothValidationError(ERR_DASHBOARD_IDS_EMPTY)
        for dashboard_id in dashboard_ids:
            _require_id("dashboard_ids", dashboard_id)
        return await self._client._request_json(
            "POST",
            f"/collections/{collection_id}/dashboards",
            json={"dashboard_ids": dashboard_ids, "notify": notify},
        )

    async def remove_dashboard(self, collection_id: int, dashboard_id: int) -> dict[str, Any]:
        """Remove a dashboard from a collection. The dashboard itself is kept.

        Args:
            collection_id: ID of the collection (must be > 0).
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            ``{"collection_id": ..., "dashboard_id": ..., "removed": True}``.

        Raises:
            MammothValidationError: If an id ≤ 0.
        """
        _require_id("collection_id", collection_id)
        _require_id("dashboard_id", dashboard_id)
        await self._client._request_json(
            "DELETE", f"/collections/{collection_id}/dashboards/{dashboard_id}"
        )
        return {"collection_id": collection_id, "dashboard_id": dashboard_id, "removed": True}

    async def share(self, collection_id: int, emails: _list[str]) -> dict[str, Any]:
        """Share a collection with people by email.

        Args:
            collection_id: ID of the collection (must be > 0).
            emails: 1 to 200 email addresses.

        Returns:
            Dict with ``added``, ``already`` (members before) and ``in_project`` (skipped:
            they already edit the project's boards).

        Raises:
            MammothValidationError: If *emails* is empty or over 200 long.
        """
        _require_id("collection_id", collection_id)
        if not emails or len(emails) > _SHARE_MAX_EMAILS:
            raise MammothValidationError(ERR_EMAILS)
        return await self._client._request_json(
            "POST", f"/collections/{collection_id}/share", json={"emails": emails}
        )

    async def remove_member(self, collection_id: int, email: str) -> dict[str, Any]:
        """Take a person off a collection.

        Args:
            collection_id: ID of the collection (must be > 0).
            email: The person's email.

        Returns:
            ``{"collection_id": ..., "email": ..., "removed": True}``.

        Raises:
            MammothValidationError: If *email* is empty.
        """
        _require_id("collection_id", collection_id)
        if not isinstance(email, str) or not email:
            raise MammothValidationError(ERR_EMAIL_EMPTY)
        await self._client._request_json(
            "DELETE", f"/collections/{collection_id}/members", params={"email": email}
        )
        return {"collection_id": collection_id, "email": email, "removed": True}

    async def for_dashboard(self, dashboard_id: int) -> dict[str, Any]:
        """List the collections that hold a dashboard.

        Args:
            dashboard_id: ID of the dashboard (must be > 0).

        Returns:
            Dict ``{"collections": [...]}``, as ``list`` returns it.

        Raises:
            MammothValidationError: If *dashboard_id* ≤ 0.
        """
        _require_id("dashboard_id", dashboard_id)
        return await self._client._request_json("GET", f"/collections/for-dashboard/{dashboard_id}")

    async def activity(self, collection_id: int) -> dict[str, Any]:
        """Get who opened a collection and which of its dashboards get opened.

        Args:
            collection_id: ID of the collection (must be > 0).

        Returns:
            Dict with ``days``, ``opened``, ``member_count``, ``people`` (email, status,
            ``last_opened_at``) and ``dashboards`` (views and viewers each).

        Raises:
            MammothValidationError: If *collection_id* ≤ 0.
        """
        _require_id("collection_id", collection_id)
        return await self._client._request_json("GET", f"/collections/{collection_id}/activity")

    async def pipeline_changes(self, collection_id: int) -> dict[str, Any]:
        """Get the progress of the collection's data refresh.

        Args:
            collection_id: ID of the collection (must be > 0).

        Returns:
            The refresh progress; empty when no automation is linked.

        Raises:
            MammothValidationError: If *collection_id* ≤ 0.
        """
        _require_id("collection_id", collection_id)
        return await self._client._request_json(
            "GET", f"/collections/{collection_id}/pipeline-changes"
        )

    async def upload_files(
        self,
        collection_id: int,
        files: _list[str],
        append_to_ds_id: int | None = None,
    ) -> dict[str, Any]:
        """Upload files to refresh the collection's data.

        Args:
            collection_id: ID of the collection (must be > 0).
            files: Local files to upload (at least one).
            append_to_ds_id: Append to this dataset of the collection's refresh.

        Returns:
            The upload job (``id``); the refresh runs in the background.

        Raises:
            MammothValidationError: If *files* is empty or a file does not exist.
        """
        _require_id("collection_id", collection_id)
        if not files:
            raise MammothValidationError(ERR_FILES_EMPTY)
        paths = [Path(f) for f in files]
        for path in paths:
            if not path.is_file():
                raise MammothValidationError(ERR_FILE_MISSING.format(path))
        if append_to_ds_id is not None:
            _require_id("append_to_ds_id", append_to_ds_id)
        handles = [path.open("rb") for path in paths]
        try:
            return await self._client._request_json(
                "POST",
                f"/collections/{collection_id}/files",
                params={"append_to_ds_id": append_to_ds_id} if append_to_ds_id else None,
                files=[
                    ("files", (os.path.basename(path), handle, "application/octet-stream"))
                    for path, handle in zip(paths, handles, strict=True)
                ],
            )
        finally:
            for handle in handles:
                handle.close()

    async def email_updates(self, collection_id: int) -> dict[str, Any]:
        """Get a collection's email updates: schedule, people, unsubscribed and a preview.

        Whether the collection's people get each dashboard's headline numbers by email,
        when, who unsubscribed, and a preview of the numbers. Managers only.

        Args:
            collection_id: ID of the collection (must be > 0).

        Returns:
            Dict with ``update`` (the saved setting, or None when never set up), ``people``,
            ``unsubscribed`` and ``boards`` (a preview of each dashboard's numbers).

        Raises:
            MammothValidationError: If *collection_id* <= 0.
        """
        _require_id("collection_id", collection_id)
        return await self._client._request_json(
            "GET", f"/collections/{collection_id}/email-updates"
        )

    async def set_email_updates(
        self,
        collection_id: int,
        enabled: bool,
        timezone: str,
        trigger: str | None = None,
        frequency: str | None = None,
        weekday: int | None = None,
        monthday: int | None = None,
        time_of_day: str | None = None,
        numbers: dict[str, _list[str]] | None = None,
    ) -> dict[str, Any]:
        """Turn a collection's email updates on or off, or change them. Managers only.

        This emails the collection's people when it runs: turn it on with care. Fields left
        as None are not sent, and the server applies its defaults (``new_data``, ``weekly``,
        ``09:00``).

        Args:
            collection_id: ID of the collection (must be > 0).
            enabled: True to send the updates, False to stop.
            timezone: IANA time zone name the schedule runs in, such as ``Europe/Paris``.
            trigger: ``new_data`` (when the data refreshes) or ``schedule``.
            frequency: ``daily``, ``weekdays``, ``weekly`` or ``monthly``.
            weekday: Day for a weekly update, 0 (Monday) to 6 (Sunday).
            monthday: Day for a monthly update, 1 to 28.
            time_of_day: Time of the update as ``HH:MM`` (24-hour).
            numbers: Dashboard id to the figure keys to include.

        Returns:
            Dict as :meth:`email_updates` returns it.

        Raises:
            MammothValidationError: If an id or a field is out of range.
        """
        _require_id("collection_id", collection_id)
        body = _email_update_body(
            enabled, timezone, trigger, frequency, weekday, monthday, time_of_day, numbers
        )
        return await self._client._request_json(
            "PUT", f"/collections/{collection_id}/email-updates", json=body
        )

    async def my_email_updates(self, collection_id: int) -> dict[str, Any]:
        """Get whether the caller receives a collection's email updates.

        Args:
            collection_id: ID of the collection (must be > 0).

        Returns:
            Dict ``{"available": bool, "subscribed": bool}``.

        Raises:
            MammothValidationError: If *collection_id* <= 0.
        """
        _require_id("collection_id", collection_id)
        return await self._client._request_json(
            "GET", f"/collections/{collection_id}/email-updates/me"
        )

    async def set_my_email_updates(self, collection_id: int, subscribed: bool) -> dict[str, Any]:
        """Turn the caller's own email updates for a collection on, or off.

        Args:
            collection_id: ID of the collection (must be > 0).
            subscribed: True to receive the updates, False to unsubscribe.

        Returns:
            Dict ``{"available": bool, "subscribed": bool}``.

        Raises:
            MammothValidationError: If *collection_id* <= 0 or *subscribed* is not a bool.
        """
        _require_id("collection_id", collection_id)
        if not isinstance(subscribed, bool):
            raise MammothValidationError(ERR_SUBSCRIBED)
        return await self._client._request_json(
            "PUT",
            f"/collections/{collection_id}/email-updates/me",
            json={"subscribed": subscribed},
        )

    async def send_test_email_update(self, collection_id: int) -> dict[str, Any]:
        """Send one test email update to the caller, with the numbers an editor sees.

        This sends a real email, to the caller only.

        Args:
            collection_id: ID of the collection (must be > 0).

        Returns:
            Dict ``{"sent": int}``.

        Raises:
            MammothValidationError: If *collection_id* <= 0.
        """
        _require_id("collection_id", collection_id)
        return await self._client._request_json(
            "POST", f"/collections/{collection_id}/email-updates/test"
        )

    async def active_job(self, collection_id: int) -> dict[str, Any]:
        """Get the collection's upload job that is still in flight, if any.

        Args:
            collection_id: ID of the collection (must be > 0).

        Returns:
            The in-flight upload job, so an interrupted upload can be resumed.

        Raises:
            MammothValidationError: If *collection_id* ≤ 0.
        """
        _require_id("collection_id", collection_id)
        return await self._client._request_json("GET", f"/collections/{collection_id}/active-job")

    async def job(self, collection_id: int, job_id: int) -> dict[str, Any]:
        """Poll one upload job of a collection.

        Args:
            collection_id: ID of the collection (must be > 0).
            job_id: ID of the upload job (must be > 0).

        Returns:
            The upload job and its state.

        Raises:
            MammothValidationError: If an id is ≤ 0.
        """
        _require_id("collection_id", collection_id)
        _require_id("job_id", job_id)
        return await self._client._request_json(
            "GET", f"/collections/{collection_id}/jobs/{job_id}"
        )
