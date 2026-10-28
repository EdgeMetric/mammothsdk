"""Appends API client: add files to an existing dataset and report what that did.

A dataset's update method decides what a new file does to its rows (see
``mammoth._pure.appends``). Uploading into a dataset therefore has steps around the
upload itself: the mode the file will run under is read or set first (the backend reads it
when the file lands), the rows and batches are read before and after, the target is waited
on until it has taken the rows in, and a mode this upload changed is put back if the upload
fails. :meth:`AppendsAPI.append` does all of it; :meth:`AppendsAPI.prepare` and
:meth:`AppendsAPI.finish` are its two halves, for a caller that sends the file itself, later
and elsewhere (a browser): what ``prepare`` returns is plain data to carry until ``finish``.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from ..client import MammothClient

from .._pure.appends import (
    EFFECTS,
    FAILED_STATUSES,
    MODE_WORDS,
    SETTLED_STATUSES,
    UnknownUpdateMethodError,
    describe_append,
    describe_update_method,
    held_back,
    match_batches,
    refuse_override,
    rows_of,
    schema_mismatches,
    sent_names,
    status_of,
    stored_mode,
    unknown_update_method,
)
from ..exceptions import MammothError, MammothJobTimeoutError, MammothValidationError

_list = list  # Alias to avoid shadowing by method name

#: How many batches the listing is read per page.
BATCH_PAGE = 100
#: The most pages of batches read, so a server that ignores ``offset`` cannot loop forever.
BATCH_PAGES = 10
#: How long :meth:`AppendsAPI.finish` waits for the target to take the rows in, and the gap
#: between its reads.
APPEND_WAIT_S = 120.0
APPEND_POLL_S = 5.0
#: The key of an exception's ``details`` that says a mode this upload set stayed.
UPDATE_METHOD_KEPT = "update_method_kept"
ERR_REFUSED = "The server refused the upload and added nothing to dataset {0}: {1}"


class AppendsAPI:
    """Client for adding files to an existing dataset.

    Access via client.appends::

        report = await client.appends.append("more.csv", dataset_id=123, mode="add")
        report["rows_added"], report["batch_ids"]
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    async def read_mode(self, dataset_id: int, project_id: int | None = None) -> dict[str, Any]:
        """Read a dataset's update method for a report; a failure is said, not raised.

        Args:
            dataset_id: ID of the dataset.
            project_id: ID of the project (uses client default if not provided).

        Returns:
            ``{"mode", "effect", "schema_mapping"}`` with ``mode`` ``add`` or ``replace``;
            when the mode cannot be read or is not a known one, ``{"mode": None,
            "effect", "error"}`` with the reason.
        """
        try:
            stored = await self._client.datasets.get_update_method(
                dataset_id, project_id=project_id
            )
            return describe_update_method(stored)
        except (MammothError, UnknownUpdateMethodError) as failure:
            return unknown_update_method(str(failure).strip() or type(failure).__name__)

    async def rows(self, dataset_id: int, project_id: int | None = None) -> int | None:
        """The dataset's stored row count, or None when it holds none."""
        return rows_of(await self._read_dataset(dataset_id, project_id))

    async def list_batches(
        self, dataset_id: int, project_id: int | None = None
    ) -> _list[dict[str, Any]]:
        """Every batch of a dataset, in listing order, paging through the listing.

        Args:
            dataset_id: ID of the dataset.
            project_id: ID of the project (uses client default if not provided).

        Returns:
            The batch rows, each with an int ``id``, without repeats. Reading stops at a
            short page, at a full page that adds no new id, or after :data:`BATCH_PAGES`
            pages.
        """
        return (await self.read_batches(dataset_id, project_id))[0]

    async def read_batches(
        self, dataset_id: int, project_id: int | None = None
    ) -> tuple[_list[dict[str, Any]], _list[dict[str, Any]]]:
        """Every batch of a dataset, and the files the server lists as waiting on it.

        Args:
            dataset_id: ID of the dataset.
            project_id: ID of the project (uses client default if not provided).

        Returns:
            ``(batches, pending)``: the batch rows as :meth:`list_batches` gives them, and the
            ``pending_batches`` of the first page (files not yet appended, among them the ones
            the server held back for a schema mismatch).
        """
        found: _list[dict[str, Any]] = []
        pending: _list[dict[str, Any]] = []
        offset = 0
        for _ in range(BATCH_PAGES):
            page = await self._client.batches.list(
                dataset_id, project_id=project_id, limit=BATCH_PAGE, offset=offset
            )
            rows = page.get("batches") if isinstance(page, dict) else page
            rows = rows if isinstance(rows, _list) else []
            if offset == 0 and isinstance(page, dict):
                waiting = page.get("pending_batches")
                pending = (
                    [row for row in waiting if isinstance(row, dict)]
                    if isinstance(waiting, _list)
                    else []
                )
            seen = {row["id"] for row in found}
            new = [
                row
                for row in rows
                if isinstance(row, dict)
                and isinstance(row.get("id"), int)
                and row["id"] not in seen
            ]
            found.extend(new)
            if len(rows) < BATCH_PAGE or not new:
                break
            offset += BATCH_PAGE
        return found, pending

    async def prepare(
        self, dataset_id: int, mode: str | None = None, project_id: int | None = None
    ) -> dict[str, Any]:
        """Read the dataset as it is before files go in, and set the mode they run under.

        The backend reads the update method when a file lands, so a mode asked for is set
        here, before the files are sent. Nothing is changed when ``mode`` is left out: the
        stored mode is read so the report can say which one the upload ran under. A dataset
        that cannot be read stops this before anything is changed.

        Args:
            dataset_id: ID of the dataset the files are added to.
            mode: ``add`` or ``replace`` to set (``combine`` and ``append`` are accepted
                for ``add``), or None to keep what the dataset holds.
            project_id: ID of the project (uses client default if not provided).

        Returns:
            Plain data for :meth:`finish`, :meth:`restore_mode` and ``describe_append``:
            ``target``, ``update_method`` (``mode``, ``effect``, ``previous_mode`` when this
            changed it, ``error`` when the stored mode could not be read), ``mode_changed``,
            ``rows_before``, ``batch_ids_before`` and ``held_back_before`` (files the server
            had already held back for a schema mismatch).

        Raises:
            MammothValidationError: If *mode* is not a known mode.
            MammothError: If the dataset cannot be read or its mode cannot be set.
        """
        asked = None
        if mode is not None:
            try:
                asked = stored_mode(mode)
            except UnknownUpdateMethodError as exc:
                raise MammothValidationError(str(exc)) from exc
        rows_before = rows_of(await self._read_dataset(dataset_id, project_id))
        batches, waiting = await self.read_batches(dataset_id, project_id)
        read = await self.read_mode(dataset_id, project_id)
        changed = False
        entry = {key: value for key, value in read.items() if key != "schema_mapping"}
        if asked is not None and read["mode"] != MODE_WORDS[asked]:
            await self._client.datasets.set_update_method(dataset_id, asked, project_id=project_id)
            changed = True
            entry = {"mode": MODE_WORDS[asked], "effect": EFFECTS[MODE_WORDS[asked]]}
            if read["mode"] is not None:
                entry["previous_mode"] = read["mode"]
            else:
                entry["previous_error"] = read["error"]
        elif asked is not None:
            entry = {"mode": read["mode"], "effect": read["effect"]}
        return {
            "target": dataset_id,
            "update_method": entry,
            "mode_changed": changed,
            "rows_before": rows_before,
            "batch_ids_before": [row["id"] for row in batches],
            "held_back_before": [item["dataset_id"] for item in held_back(waiting, dataset_id)],
        }

    async def finish(
        self,
        plan: dict[str, Any],
        file_names: _list[str],
        staging_ids: _list[int] | None = None,
        wait_seconds: float = APPEND_WAIT_S,
        poll_seconds: float = APPEND_POLL_S,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Wait for the rows to land in the dataset, then report what the upload did.

        The upload job ends when its staging dataset is made; the rows reach the target
        after that, and the target can still read ready before it starts on them. So the
        rows count as landed once the target is ready and lists a batch it did not have.

        Args:
            plan: What :meth:`prepare` returned before the files were sent.
            file_names: The names of the files that were sent.
            staging_ids: The staging dataset ids the upload made, when known: a batch
                sourced from one of them is the upload's.
            wait_seconds: The longest to wait for the dataset to settle.
            poll_seconds: The longest gap between reads of the dataset.
            project_id: ID of the project (uses client default if not provided).

        Returns:
            ``appended_to``, ``update_method``, ``rows_before``, ``rows_after``,
            ``rows_added``, ``batch_ids`` (the upload's own batches), ``unmatched_batch_ids``
            (new batches not tied to it), and ``append_pending`` when the dataset had not
            taken the rows in by the end of the wait (``read_error`` says why when the dataset
            could not be read), and ``append_failed`` with ``status`` when the dataset ended
            in a failed status. What could not be read is left out; ``batches_error`` says
            why the batches are missing.
        """
        dataset_id = int(plan["target"])
        before = set(plan["batch_ids_before"])
        give_up_at = time.monotonic() + max(0.0, wait_seconds)
        gap = min(0.5, poll_seconds)
        settled = False
        rows_after: int | None = None
        status: str | None = None
        read_error: str | None = None
        after: _list[dict[str, Any]] = []
        mismatched: _list[int] = []
        batches_error: str | None = None
        while True:
            try:
                read = await self._read_dataset(dataset_id, project_id)
                read_error = None
            except MammothError as failure:
                read = {}
                read_error = str(failure).strip() or type(failure).__name__
            status = status_of(read)
            rows_after = rows_of(read)
            if status in FAILED_STATUSES:
                settled = True
            elif status in SETTLED_STATUSES:
                # The upload job ends before the target starts taking the rows in, so a
                # ready target may not have them yet: it has them once their batch is listed.
                try:
                    after, waiting = await self.read_batches(dataset_id, project_id)
                    batches_error = None
                    # A file whose columns do not match is never appended: the server flags
                    # it on its pending item, which is the only record of why no batch came.
                    mismatched = schema_mismatches(
                        waiting,
                        dataset_id,
                        plan.get("held_back_before", []),
                        staging_ids or [],
                        file_names,
                    )
                except MammothError as failure:
                    batches_error = str(failure).strip() or type(failure).__name__
                settled = bool(mismatched) or any(row["id"] not in before for row in after)
            if settled or time.monotonic() >= give_up_at:
                break
            await asyncio.sleep(gap)
            gap = min(gap * 2, poll_seconds)
        if batches_error is not None:
            report = describe_append(plan, rows_after, [], [], settled, status, read_error)
            report.pop("batch_ids")
            report["batches_error"] = batches_error
            return report
        ours, unmatched = match_batches(list(before), after, file_names, staging_ids or [])
        return describe_append(
            plan, rows_after, ours, unmatched, settled, status, read_error, mismatched
        )

    async def restore_mode(self, plan: dict[str, Any], project_id: int | None = None) -> str | None:
        """Put the dataset's mode back after the upload that needed it failed (best effort).

        Args:
            plan: What :meth:`prepare` returned.
            project_id: ID of the project (uses client default if not provided).

        Returns:
            None when nothing needed putting back or it was put back; otherwise a sentence
            saying the new mode stayed and why.
        """
        if not plan.get("mode_changed"):
            return None
        dataset_id = int(plan["target"])
        entry = plan["update_method"]
        note = (
            f"Dataset {dataset_id} kept the update method {entry.get('mode')} this upload gave"
            " it, because the old one could not be restored"
        )
        previous = entry.get("previous_mode")
        if previous is None:
            return f"{note} (it was not known)."
        try:
            await self._client.datasets.set_update_method(
                dataset_id, stored_mode(previous), project_id=project_id
            )
        except (MammothError, UnknownUpdateMethodError) as failure:
            return f"{note} ({str(failure).strip() or type(failure).__name__})."
        return None

    async def append(
        self,
        files: _list[str | Path | BinaryIO] | str | Path | BinaryIO,
        dataset_id: int,
        mode: str | None = None,
        folder_resource_id: str | int | None = None,
        override_target_schema: bool | None = None,
        timeout: int = 300,
        wait_seconds: float = APPEND_WAIT_S,
        poll_seconds: float = APPEND_POLL_S,
    ) -> dict[str, Any]:
        """Add files to an existing dataset and report what that did to it.

        Reads (or sets) the update method, reads the rows and batches, uploads with
        ``FilesAPI.upload_result(append_to_ds_id=...)``, waits for the dataset to take the
        rows in, and reads rows and batches again. If the upload fails, a mode this call
        changed is put back, best effort; a mode that could not be put back is named in
        the raised error's ``details["update_method_kept"]``.

        Args:
            files: File(s) to add: paths, Path objects, or file-like objects.
            dataset_id: ID of the dataset to add them to.
            mode: ``add`` or ``replace`` to set first, or None to keep the dataset's own.
                A mode set stays on the dataset: every later upload follows it.
            folder_resource_id: Resource ID of the target folder.
            override_target_schema: Make the file's columns the dataset's. The server applies
                this only when the dataset's update method is ``replace`` (which deletes the
                rows it holds), so any other method is refused before anything is sent.
            timeout: Timeout in seconds for the upload job.
            wait_seconds: The longest to wait for the dataset to settle afterwards.
            poll_seconds: The longest gap between reads of the dataset.

        Returns:
            ``FilesAPI.upload_result``'s fields (``job_id``, ``dataset_ids`` of the staging
            datasets, ``errors``, ``nested_job_ids``, ``files``, ``files_error``) and
            :meth:`finish`'s: ``appended_to``, ``update_method``, ``rows_before``,
            ``rows_after``, ``rows_added``, ``batch_ids``, ``unmatched_batch_ids``,
            ``append_pending``; ``append_failed`` with ``failure`` ``schema_mismatch``,
            ``reason``, ``kept_dataset_ids`` and ``next_step`` when the server held the file
            back because its columns do not match (nothing was added; the file's own dataset
            stays in the project).

        Raises:
            MammothValidationError: If *mode* is unknown, *override_target_schema* is asked
                for under a method other than ``replace``, or the server refused the files
                and added nothing.
            MammothJobTimeoutError: If the upload job outlasted *timeout*. The mode is not
                put back: the job still runs and reads it when the file lands.
            MammothError: Any other refusal, after the mode was put back.
        """
        plan = await self.prepare(dataset_id, mode)
        refusal = refuse_override(override_target_schema, plan["update_method"].get("mode"))
        if refusal:
            kept = await self.restore_mode(plan)
            raise MammothValidationError(
                refusal, details={UPDATE_METHOD_KEPT: kept} if kept else None
            )
        try:
            outcome = await self._client.files.upload_result(
                files,
                folder_resource_id=folder_resource_id,
                append_to_ds_id=dataset_id,
                override_target_schema=override_target_schema,
                timeout=timeout,
            )
            if outcome["errors"] and not outcome["dataset_ids"]:
                raise MammothValidationError(
                    ERR_REFUSED.format(dataset_id, outcome["errors"]),
                    details={"errors": outcome["errors"]},
                )
        except MammothJobTimeoutError:
            raise
        except MammothError as failure:
            kept = await self.restore_mode(plan)
            if kept:
                failure.details[UPDATE_METHOD_KEPT] = kept
            raise
        report = await self.finish(
            plan,
            sent_names(files),
            outcome["dataset_ids"],
            wait_seconds=wait_seconds,
            poll_seconds=poll_seconds,
        )
        return {**outcome, **report}

    async def _read_dataset(self, dataset_id: int, project_id: int | None) -> dict[str, Any]:
        """The dataset with its status and row counts."""
        return await self._client.datasets.get(
            dataset_id, project_id=project_id, fields="__standard"
        )
