"""Workflow describe API client: say what a workflow should do, read it back, build it."""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from mammoth.api.workflow_triggers import schedule_body
from mammoth.api.workflows import check_timeout
from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient


ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_TEXT = "`text` must be 3 to 2000 characters."
ERR_DATASET_IDS = "`dataset_ids` must be at most 10 positive dataset ids, got {0!r}."
ERR_DRAFT = "`draft` must be the non-empty draft id `start` returned."
ERR_SPEC = "`spec` must be the read-back's spec (a dict)."
ERR_DESTINATION = "`destination_name` must be 1 to 120 characters."
ERR_VIEW_ID = "`view_id` must be a positive integer, got {0!r}."
ERR_FILE = "File not found: {0}"
ERR_SCHEDULE = "`schedule` must be a clock: {frequency, interval?, by_week_day?, ...}."
_TEXT_MIN, _TEXT_MAX = 3, 2000
_DATASETS_MAX = 10
_DESTINATION_MAX = 120
#: A draft still being read back.
DRAFT_RUNNING = "running"
_POLL_SECONDS = 2.0


class WorkflowDescribeAPI:
    """Client for describing a workflow in words and building what is read back.

    ``start`` hands the description to the model and returns a draft id at once;
    ``draft`` (or ``describe(wait=True)``) reads it back: the workflow's sentence, the
    tables it reads, its steps, its result on your rows, at most two questions, and
    ``template_key`` when a catalog template (``client.workflow_templates``) is exactly
    the job. ``build`` adds the read-back's steps to a new workflow and starts its Save.

    Access via ``client.workflow_describe``::

        state = await client.workflow_describe.describe(
            "Match Stripe payouts to the bank feed", dataset_ids=[812, 815], wait=True
        )
        spec = state["read_back"]["spec"]
        built = await client.workflow_describe.build(spec, "Payout matches")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _base(self, project_id: int | None) -> str:
        if project_id is not None and project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        proj = project_id if project_id is not None else getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        return f"/workspaces/{self._client.workspace_id}/projects/{proj}/workflows/describe"

    async def start(
        self,
        text: str,
        *,
        dataset_ids: list[int] | None = None,
        name: str | None = None,
        answers: list[dict[str, str]] | None = None,
        samples: list[str] | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Start reading a description back as a workflow; returns its draft id at once.

        Args:
            text: What the workflow should do (3 to 2000 characters).
            dataset_ids: Tables it should read (at most 10).
            name: The draft's name so far; a redraft keeps it.
            answers: Answers to the read-back's questions, ``{"question", "answer"}``
                each; send them with the same *text* to redraft.
            samples: Ids of files kept with ``keep_sample`` (files that arrive).
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"draft", "state": "running"}``.

        Raises:
            MammothValidationError: If *text* or *dataset_ids* is out of range.
        """
        body = describe_body(text, dataset_ids=dataset_ids, name=name, answers=answers)
        if samples:
            body["samples"] = samples
        return await self._client._request_json("POST", self._base(project_id), json=body)

    async def draft(self, draft: str, project_id: int | None = None) -> dict[str, Any]:
        """Read a draft: ``state`` running, done (with ``read_back``) or failed (``reason``).

        Args:
            draft: The draft id ``start`` returned.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"draft", "state", "read_back", "reason"}``. The read-back holds the
            ``spec`` (status ready, needs_source or unclear; at most two ``asks``;
            ``template_key``), the steps and the result on your rows.

        Raises:
            MammothValidationError: If *draft* is empty.
        """
        if not isinstance(draft, str) or not draft.strip():
            raise MammothValidationError(ERR_DRAFT)
        return await self._client._request_json(
            "GET", f"{self._base(project_id)}/{quote(draft.strip(), safe='')}"
        )

    async def wait(
        self, draft: str, *, timeout: float = 120.0, project_id: int | None = None
    ) -> dict[str, Any]:
        """Poll a draft until it is done or failed, or *timeout* passes.

        Args:
            draft: The draft id ``start`` returned.
            timeout: Seconds to wait; ``0`` reads once.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The draft's latest state; ``state`` is still ``running`` when the wait ended
            first.

        Raises:
            MammothValidationError: If *draft* is empty or *timeout* is negative.
        """
        check_timeout(timeout)
        deadline = time.monotonic() + timeout
        while True:
            state = await self.draft(draft, project_id=project_id)
            left = deadline - time.monotonic()
            if state.get("state") != DRAFT_RUNNING or left <= 0:
                return state
            await asyncio.sleep(min(_POLL_SECONDS, left))

    async def describe(
        self,
        text: str,
        *,
        dataset_ids: list[int] | None = None,
        name: str | None = None,
        answers: list[dict[str, str]] | None = None,
        wait: bool = True,
        timeout: float = 120.0,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Describe a workflow and, by default, wait for its read-back.

        Args:
            text: What the workflow should do (3 to 2000 characters).
            dataset_ids: Tables it should read (at most 10).
            name: The draft's name so far.
            answers: Answers to the read-back's questions.
            wait: Poll the draft until it is done or failed, or *timeout* passes.
            timeout: Seconds to wait when *wait* is true.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The draft's state (see ``draft``); ``{"draft", "state": "running"}`` without
            *wait*.

        Raises:
            MammothValidationError: If an argument is out of range.
        """
        started = await self.start(
            text, dataset_ids=dataset_ids, name=name, answers=answers, project_id=project_id
        )
        if not wait:
            return started
        return await self.wait(str(started["draft"]), timeout=timeout, project_id=project_id)

    async def check(
        self,
        spec: dict[str, Any],
        *,
        samples: list[str] | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Read an edited spec back on its tables again, with no model call.

        Args:
            spec: A read-back's spec, edited.
            samples: Ids of files kept with ``keep_sample``.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The read-back for *spec*.

        Raises:
            MammothValidationError: If *spec* is not a dict.
        """
        if not isinstance(spec, dict) or not spec:
            raise MammothValidationError(ERR_SPEC)
        body: dict[str, Any] = {"spec": spec}
        if samples:
            body["samples"] = samples
        return await self._client._request_json(
            "POST", f"{self._base(project_id)}/check", json=body
        )

    async def build(
        self,
        spec: dict[str, Any],
        destination_name: str,
        *,
        destination_emails: list[str] | None = None,
        schedule: dict[str, Any] | None = None,
        samples: list[str] | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Add a read-back's steps to a new workflow and start the Save that builds them.

        People the description said to email the result to are added to
        *destination_emails*. A draft of files that arrive makes its spreadsheet, folder
        and automation instead.

        Args:
            spec: The read-back's spec (``draft(...)["read_back"]["spec"]``).
            destination_name: The result table's name (1 to 120 characters).
            destination_emails: People to email the result to after each run.
            schedule: A clock to turn on with the Save, as ``schedule_set`` takes it
                (``{"frequency": "weekly", "by_week_day": ["mo"]}``).
            samples: Ids of files kept with ``keep_sample``.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            Dict with the ``workflow`` whose ``canvas_state.save_run`` is the Save in
            progress (poll ``client.workflows.get``).

        Raises:
            MammothValidationError: If an argument is invalid.
        """
        body = build_body(
            spec, destination_name, destination_emails=destination_emails, schedule=schedule
        )
        if samples:
            body["samples"] = samples
        return await self._client._request_json(
            "POST", f"{self._base(project_id)}/build", json=body
        )

    async def keep_sample(self, file: str | Path, project_id: int | None = None) -> dict[str, Any]:
        """Keep a file to try a draft of files that arrive on (receipts, invoices).

        Args:
            file: Local path of the file.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The kept file's id, to pass as ``samples``.

        Raises:
            MammothValidationError: If the file cannot be read.
        """
        path = Path(file)
        if not path.is_file():
            raise MammothValidationError(ERR_FILE.format(path))
        with path.open("rb") as opened:
            return await self._client._request_json(
                "POST",
                f"{self._base(project_id)}/samples",
                files=[("file", (os.path.basename(path), opened, "application/octet-stream"))],
            )

    async def fed_by(self, view_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Find the workflow that feeds a board on a view.

        Args:
            view_id: ID of the view.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The workflow feeding the view, as the server describes it.

        Raises:
            MammothValidationError: If *view_id* is not positive.
        """
        if isinstance(view_id, bool) or not isinstance(view_id, int) or view_id <= 0:
            raise MammothValidationError(ERR_VIEW_ID.format(view_id))
        return await self._client._request_json("GET", f"{self._base(project_id)}/fed-by/{view_id}")


def describe_body(
    text: str,
    *,
    dataset_ids: list[int] | None = None,
    name: str | None = None,
    answers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build and check the body of ``POST .../workflows/describe``.

    Args:
        text: What the workflow should do (3 to 2000 characters).
        dataset_ids: Tables it should read (at most 10).
        name: The draft's name so far.
        answers: Answers to the read-back's questions.

    Returns:
        The request body, with only the fields given.

    Raises:
        MammothValidationError: If *text* or *dataset_ids* is out of range.
    """
    said = text.strip() if isinstance(text, str) else ""
    if not _TEXT_MIN <= len(said) <= _TEXT_MAX:
        raise MammothValidationError(ERR_TEXT)
    body: dict[str, Any] = {"text": said}
    if dataset_ids is not None:
        bad = not isinstance(dataset_ids, list) or len(dataset_ids) > _DATASETS_MAX
        if bad or any(isinstance(i, bool) or not isinstance(i, int) or i <= 0 for i in dataset_ids):
            raise MammothValidationError(ERR_DATASET_IDS.format(dataset_ids))
        body["dataset_ids"] = dataset_ids
    if name:
        body["name"] = name
    if answers:
        body["answers"] = answers
    return body


def build_body(
    spec: dict[str, Any] | None,
    destination_name: str,
    *,
    destination_emails: list[str] | None = None,
    schedule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and check the body of ``POST .../workflows/describe/build``.

    Args:
        spec: The read-back's spec.
        destination_name: The result table's name (1 to 120 characters).
        destination_emails: People to email the result to after each run.
        schedule: A clock, as ``WorkflowTriggersAPI.schedule_set`` takes it.

    Returns:
        The request body, with the clock checked and filled in.

    Raises:
        MammothValidationError: If *spec*, *destination_name* or *schedule* is invalid.
    """
    if not isinstance(spec, dict) or not spec:
        raise MammothValidationError(ERR_SPEC)
    name = destination_name.strip() if isinstance(destination_name, str) else ""
    if not 1 <= len(name) <= _DESTINATION_MAX:
        raise MammothValidationError(ERR_DESTINATION)
    body: dict[str, Any] = {
        "spec": spec,
        "destination": {"name": name, "emails": destination_emails or []},
    }
    if schedule is not None:
        if not isinstance(schedule, dict):
            raise MammothValidationError(ERR_SCHEDULE)
        try:
            body["schedule"] = schedule_body(**schedule)
        except TypeError as exc:
            raise MammothValidationError(ERR_SCHEDULE) from exc
    return body
