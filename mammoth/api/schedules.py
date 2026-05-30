"""Schedules API client for managing project schedules in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.api.automations import (
    ERR_SCHEDULE_ID_POSITIVE,
    ERR_SCHEDULE_PATCH_EMPTY,
    SchedulePatchItem,
    _rrule_spec_to_dict,
    _validate_schedule_create,
    build_schedule_patch_ops,
)
from mammoth.exceptions import MammothValidationError
from mammoth.models.automations import ScheduleCreateSpec

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."


class SchedulesAPI:
    """Client for managing schedules under projects.

    Access via ``client.schedules``::

        schedules = client.schedules.list()
        schedule = client.schedules.create(
            spec=ScheduleCreateSpec(
                rrule=RruleSpec(frequency=RruleFrequency.DAILY, start=datetime(2025, 1, 1)),
            )
        )
        client.schedules.delete(schedule_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self, project_id: int | None = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, "project_id", None)
        if proj is not None:
            return proj
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    def list(
        self,
        project_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List schedules in a project.

        .. note::

            The server may not support listing all schedules (HTTP 405).
            Use :meth:`get` to retrieve individual schedules by ID.

        Args:
            project_id: Project ID (uses client default if not provided).
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).

        Returns:
            Dict with schedules list and pagination info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {}
        if limit != 50:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/schedules",
            params=params or None,
        )

    def get(self, schedule_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Get schedule details.

        Args:
            schedule_id: ID of the schedule.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with schedule details.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET", f"/workspaces/{ws}/projects/{proj}/schedules/{schedule_id}"
        )

    def create(
        self,
        spec: ScheduleCreateSpec,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new schedule.

        Args:
            spec: :class:`~mammoth.models.automations.ScheduleCreateSpec` describing
                the recurrence rule and optional work items.
            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with created schedule info.

        Raises:
            MammothValidationError: If *project_id* ≤ 0 or ``rrule.interval`` ≤ 0.
        """
        if project_id is not None and project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        _validate_schedule_create(spec)
        ws = self._ws()
        proj = self._proj(project_id)
        body = _rrule_spec_to_dict(spec)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/schedules",
            json=body,
        )

    def update(
        self,
        schedule_id: int,
        patch: _list[SchedulePatchItem],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a schedule via JSON-patch operations.

        Args:
            schedule_id: ID of the schedule (must be > 0).
            patch: Non-empty list of :class:`~mammoth.api.automations.SchedulePatchItem`.

                Supported combos:

                * ``op=replace, path=rrule`` — update recurrence rule + work items;
                  ``value`` must be a
                  :class:`~mammoth.models.automations.SchedulePatchValue`.
                * ``op=replace, path=status`` — pause or resume; ``value`` must
                  be ``"pause"`` or ``"resume"``.

            project_id: Project ID (uses client default if not provided; must
                be > 0 if given).

        Returns:
            Dict with updated schedule info.

        Raises:
            MammothValidationError: If *schedule_id* ≤ 0, *project_id* ≤ 0,
                *patch* is empty, or an op+path+value combination is invalid.
        """
        if schedule_id <= 0:
            raise MammothValidationError(ERR_SCHEDULE_ID_POSITIVE.format(schedule_id))
        if project_id is not None and project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        if not patch:
            raise MammothValidationError(ERR_SCHEDULE_PATCH_EMPTY)

        ws = self._ws()
        proj = self._proj(project_id)
        ops = build_schedule_patch_ops(patch)
        body: dict[str, Any] = {"patch": ops}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/schedules/{schedule_id}",
            json=body,
        )

    def delete(self, schedule_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Delete a schedule.

        Args:
            schedule_id: ID of the schedule.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/schedules/{schedule_id}",
        )
