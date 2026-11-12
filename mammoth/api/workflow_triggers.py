"""Workflow triggers API client: run a workflow now, on a clock, after another, or by link."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from mammoth.api.workflows import check_positive_id, check_timeout, workflow_path
from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

ERR_FREQUENCY = "`frequency` must be one of hourly, daily, weekly, monthly; got {0!r}."
ERR_INTERVAL = "`interval` must be an integer from 1 to 366, got {0!r}."
ERR_WEEK_DAYS = "`by_week_day` must be a list of mo, tu, we, th, fr, sa, su; got {0!r}."
ERR_MONTH_DAYS = "`by_month_day` must be a list of days 1 to 31, got {0!r}."
FREQUENCIES = ("hourly", "daily", "weekly", "monthly")
WEEK_DAYS = ("mo", "tu", "we", "th", "fr", "sa", "su")
#: How a run ends, as Recent runs says it.
RUN_RUNNING = "running"
_POLL_SECONDS = 3.0


class WorkflowTriggersAPI:
    """Client for what starts a workflow: Run now, a clock, another workflow, a link.

    Each trigger is stored as an automation (``client.automations``): pause, resume or
    remove a clock or an "after" there, by the ``automation_id`` the setter returns.
    The link has its own ``link_remove``. ``runs`` lists every kind of run, newest
    first.

    Access via ``client.workflow_triggers``::

        started = await client.workflow_triggers.run(41, wait=True)
        await client.workflow_triggers.schedule_set(41, "weekly", by_week_day=["mo"])
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _path(self, workflow_id: int, project_id: int | None, tail: str) -> str:
        return workflow_path(self._client, workflow_id, project_id, tail)

    async def run(
        self,
        workflow_id: int,
        *,
        wait: bool = False,
        timeout: float = 600.0,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Run a workflow on the server now, as its clock would.

        A workflow already running is not started twice: ``already_running`` is true
        and ``run_id`` names the run in flight.

        Args:
            workflow_id: ID of the workflow.
            wait: Poll Recent runs until the run ends or *timeout* passes.
            timeout: Seconds to wait when *wait* is true.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"run_id", "already_running"}``; with *wait*, also ``run`` (the Recent runs
            row, or ``None`` before it shows) and ``result``: ``running`` (still running
            when the wait ended), ``success`` or ``failure``.

        Raises:
            MammothValidationError: If an id is not positive or *timeout* is negative.
        """
        # Checked before the POST: a refused wait must not leave a run started.
        if wait:
            check_timeout(timeout)
        started = await self._client._request_json(
            "POST", self._path(workflow_id, project_id, "run")
        )
        if not wait:
            return started
        row = await self.wait_for_run(
            workflow_id, str(started["run_id"]), timeout=timeout, project_id=project_id
        )
        result = row["result"] if row else RUN_RUNNING
        return {**started, "run": row, "result": result}

    async def wait_for_run(
        self,
        workflow_id: int,
        run_id: str,
        *,
        timeout: float = 600.0,
        project_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Poll Recent runs until the run ends or *timeout* passes.

        Args:
            workflow_id: ID of the workflow.
            run_id: The run's id (``run`` returns it).
            timeout: Seconds to wait; ``0`` reads once.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The run's latest row (``result`` running, success or failure), or ``None``
            when it has not shown in Recent runs yet.

        Raises:
            MammothValidationError: If *timeout* is negative.
        """
        check_timeout(timeout)
        deadline = time.monotonic() + timeout
        while True:
            rows = (await self.runs(workflow_id, project_id=project_id))["runs"]
            row = next((r for r in rows if r.get("id") == run_id), None)
            left = deadline - time.monotonic()
            if (row is not None and row.get("result") != RUN_RUNNING) or left <= 0:
                return row
            await asyncio.sleep(min(_POLL_SECONDS, left))

    async def runs(self, workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
        """List a workflow's recent runs of every kind, newest first.

        Args:
            workflow_id: ID of the workflow.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"runs": [...]}``: ``id``, ``trigger`` (manual, schedule, file, after,
            called), ``result`` (running, success, failure), ``started_at``,
            ``finished_at``, ``seconds``, ``rows_out``, ``reason``. The backend answers
            with a bare JSON array, which is wrapped.

        Raises:
            MammothValidationError: If an id is not positive.
        """
        rows = await self._client._request_list("GET", self._path(workflow_id, project_id, "runs"))
        return {"runs": rows}

    async def schedule_set(
        self,
        workflow_id: int,
        frequency: str,
        *,
        interval: int = 1,
        by_week_day: list[str] | None = None,
        by_month_day: list[int] | None = None,
        start_at: str | None = None,
        start_now: bool = True,
        until: str | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Run a workflow on a clock (replaces its clock if it has one).

        Args:
            workflow_id: ID of the workflow.
            frequency: ``hourly``, ``daily``, ``weekly`` or ``monthly``.
            interval: Every how many of *frequency* (1 to 366).
            by_week_day: Days for a weekly clock (``mo`` .. ``su``).
            by_month_day: Days of the month for a monthly clock (1 to 31).
            start_at: First run, ISO 8601 in UTC (``2026-11-10T07:00:00Z``).
            start_now: Run once now as well.
            until: Last day the clock runs, ISO 8601.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"automation_id"}``: pause, resume or remove it with ``client.automations``.

        Raises:
            MammothValidationError: If an argument is out of range.
        """
        body = schedule_body(
            frequency,
            interval=interval,
            by_week_day=by_week_day,
            by_month_day=by_month_day,
            start_at=start_at,
            start_now=start_now,
            until=until,
        )
        return await self._client._request_json(
            "PUT", self._path(workflow_id, project_id, "schedule"), json=body
        )

    async def after_set(
        self,
        workflow_id: int,
        source_workflow_id: int,
        *,
        only_when_ok: bool = True,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Run a workflow each time another one finishes.

        The server refuses a source that would make a loop; ``after_loops`` names them.

        Args:
            workflow_id: ID of the workflow to start.
            source_workflow_id: ID of the workflow whose end starts it.
            only_when_ok: Start only when the source run succeeded.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"automation_id"}``: pause, resume or remove it with ``client.automations``.

        Raises:
            MammothValidationError: If an id is not positive.
        """
        check_positive_id("source_workflow_id", source_workflow_id)
        return await self._client._request_json(
            "PUT",
            self._path(workflow_id, project_id, "after"),
            json={"source_workflow_id": source_workflow_id, "only_when_ok": bool(only_when_ok)},
        )

    async def after_loops(self, workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
        """List the workflows this one cannot be set to start after (each would loop).

        Args:
            workflow_id: ID of the workflow.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"would_loop": [workflow ids]}``.

        Raises:
            MammothValidationError: If an id is not positive.
        """
        return await self._client._request_json("GET", self._path(workflow_id, project_id, "after"))

    async def link_create(self, workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Make the workflow's secret link (a new one replaces the old).

        Anyone with the link can start the workflow with ``POST`` and no sign-in. The
        secret is shown only in this answer.

        Args:
            workflow_id: ID of the workflow.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"automation_id", "made_at", "path", "secret"}``; ``path`` is the link
            under the API root.

        Raises:
            MammothValidationError: If an id is not positive.
        """
        return await self._client._request_json("POST", self._path(workflow_id, project_id, "link"))

    async def link_remove(self, workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Turn the workflow's secret link off; it stops working at once.

        Args:
            workflow_id: ID of the workflow.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            An empty dict (the server answers 204).

        Raises:
            MammothValidationError: If an id is not positive.
        """
        return await self._client._request_json(
            "DELETE", self._path(workflow_id, project_id, "link")
        )


def schedule_body(
    frequency: str,
    *,
    interval: int = 1,
    by_week_day: list[str] | None = None,
    by_month_day: list[int] | None = None,
    start_at: str | None = None,
    start_now: bool = True,
    until: str | None = None,
) -> dict[str, Any]:
    """Build and check a workflow clock (the body of ``PUT .../schedule``).

    Args:
        frequency: ``hourly``, ``daily``, ``weekly`` or ``monthly``.
        interval: Every how many of *frequency* (1 to 366).
        by_week_day: Days for a weekly clock (``mo`` .. ``su``).
        by_month_day: Days of the month for a monthly clock (1 to 31).
        start_at: First run, ISO 8601 in UTC.
        start_now: Run once now as well.
        until: Last day the clock runs, ISO 8601.

    Returns:
        The request body, with only the fields given.

    Raises:
        MammothValidationError: If an argument is out of range.
    """
    if frequency not in FREQUENCIES:
        raise MammothValidationError(ERR_FREQUENCY.format(frequency))
    if isinstance(interval, bool) or not isinstance(interval, int) or not 1 <= interval <= 366:
        raise MammothValidationError(ERR_INTERVAL.format(interval))
    body: dict[str, Any] = {"frequency": frequency, "interval": interval, "start_now": start_now}
    if by_week_day is not None:
        if not isinstance(by_week_day, list) or any(d not in WEEK_DAYS for d in by_week_day):
            raise MammothValidationError(ERR_WEEK_DAYS.format(by_week_day))
        body["by_week_day"] = by_week_day
    if by_month_day is not None:
        bad = not isinstance(by_month_day, list) or any(
            isinstance(d, bool) or not isinstance(d, int) or not 1 <= d <= 31 for d in by_month_day
        )
        if bad:
            raise MammothValidationError(ERR_MONTH_DAYS.format(by_month_day))
        body["by_month_day"] = by_month_day
    if start_at is not None:
        body["start_at"] = start_at
    if until is not None:
        body["until"] = until
    return body
