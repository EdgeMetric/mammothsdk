"""
Jobs API client for tracking job status in Mammoth.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..exceptions import (
    MammothAPIError,
    MammothJobFailedError,
    MammothJobTimeoutError,
    safe_response_body,
)

if TYPE_CHECKING:
    from ..client import MammothClient


class JobsAPI:
    """Client for interacting with Mammoth Jobs API."""

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def get_job(self, job_id: int, timeout: float | None = None) -> dict[str, Any]:
        """
        Get job status by ID.

        Args:
            job_id: ID of the job to track
            timeout: Maximum time for this observation request.  Waiters pass
                their remaining polling budget so one request cannot exceed it.

        Returns:
            Dict containing job information including status, response, timestamps

        Raises:
            MammothAPIError: If the API request fails
        """
        workspace_id = self._client.workspace_id

        headers = {"x-workspace-id": str(workspace_id)}

        request_timeout = self._observation_timeout(timeout)
        response = self._client._request_json(
            "GET", f"/jobs/{job_id}", headers=headers, **request_timeout
        )
        return response

    def get_jobs(self, job_ids: list[int] | str, timeout: float | None = None) -> dict[str, Any]:
        """
        Track multiple job IDs.

        Args:
            job_ids: List of job IDs or comma-separated string of job IDs

        Returns:
            Dict containing jobs list with status information

        Raises:
            MammothAPIError: If the API request fails
        """
        workspace_id = self._client.workspace_id

        # Convert list to comma-separated string if needed
        if isinstance(job_ids, list):
            job_ids_str = ",".join(str(job_id) for job_id in job_ids)
        else:
            job_ids_str = str(job_ids)

        params = {"job_ids": job_ids_str}

        headers = {"x-workspace-id": str(workspace_id)}

        request_timeout = self._observation_timeout(timeout)
        response = self._client._request_json(
            "GET", "/jobs", params=params, headers=headers, **request_timeout
        )
        return response

    @staticmethod
    def _observation_timeout(timeout: float | None) -> dict[str, float]:
        """Return a valid request timeout without silently dropping zero."""
        if timeout is None:
            return {}
        if timeout <= 0:
            raise ValueError("observation timeout must be positive")
        return {"timeout": timeout}

    def wait_for_job(
        self,
        job_id: int,
        timeout: float | None = None,
        poll_interval: float = 2,
        fetch: Callable[[int, float], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Wait for a job to complete and return the result.

        Args:
            job_id: ID of the job to wait for
            timeout: Maximum time to wait in seconds (default: client.job_timeout)
            poll_interval: Time between polling attempts in seconds (default: 2)
            fetch: Optional observer ``(job_id, remaining_timeout) -> job dict``
                used instead of ``GET /jobs/{id}``. Published-dashboard jobs
                are only readable through the URL-scoped job route, for
                example, and ``GET /jobs/{id}`` answers ``4PERM002`` for them.

        Returns:
            Dict containing the completed job information

        Raises:
            MammothJobFailedError: If the job fails.
            MammothJobTimeoutError: If the job does not complete within timeout.
            MammothAPIError: If the API request fails.
        """
        if timeout is None:
            timeout = getattr(self._client, "job_timeout", 60)
        if timeout is None:
            raise TypeError("timeout must not be None — set client.job_timeout or pass explicitly")

        deadline = time.monotonic() + timeout
        last_observed: dict[str, Any] | None = None
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            job_response = (
                fetch(job_id, remaining)
                if fetch is not None
                else self.get_job(job_id, timeout=remaining)
            )

            # Extract job from response
            if "job" in job_response:
                job = job_response["job"]
            else:
                job = job_response

            # Keep only the latest server observation for timeout/failure
            # diagnostics.  The exception sanitizer strips credential fields
            # before this is exposed to callers.
            last_observed = safe_response_body(job)

            status = job.get("status")
            observed_phase = job.get("phase") or job.get("execution_phase") or "polling"
            if not isinstance(observed_phase, str):
                observed_phase = "polling"

            if status == "success":
                return job
            elif status in ["failure", "error"]:
                resp = job.get("response", {})
                # Error may be at resp.error, resp.response.detail, or resp.response.error
                error_msg = resp.get("error")
                if not error_msg and isinstance(resp.get("response"), dict):
                    inner = resp["response"]
                    error_msg = inner.get("detail") or inner.get("error")
                error_msg = error_msg or "Job failed"
                raise MammothJobFailedError(
                    job_id,
                    error_msg,
                    observed_job=last_observed,
                    phase=observed_phase,
                )
            elif status == "processing":
                # Job still running, continue polling
                time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
            else:
                # Unknown status, continue polling
                time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))

        # Timeout reached
        timeout_phase = "polling"
        if last_observed is not None:
            candidate_phase = last_observed.get("phase") or last_observed.get("execution_phase")
            if isinstance(candidate_phase, str):
                timeout_phase = candidate_phase
        raise MammothJobTimeoutError(
            job_id, timeout, observed_job=last_observed, phase=timeout_phase
        )

    def wait_for_jobs(
        self, job_ids: list[int] | str, timeout: int | None = None, poll_interval: int = 2
    ) -> dict[str, Any]:
        """
        Wait for multiple jobs to complete.

        Args:
            job_ids: List of job IDs or comma-separated string
            timeout: Maximum time to wait in seconds (default: client.job_timeout)
            poll_interval: Time between polling attempts in seconds (default: 2)

        Returns:
            Dict containing all completed jobs information

        Raises:
            MammothJobFailedError: If any job fails.
            MammothJobTimeoutError: If jobs do not complete within timeout.
            MammothAPIError: If the API request fails.
        """
        if timeout is None:
            timeout = getattr(self._client, "job_timeout", 60)
        if timeout is None:
            raise TypeError("timeout must not be None — set client.job_timeout or pass explicitly")

        # Convert to list if string
        if isinstance(job_ids, str):
            job_ids_list = [int(x.strip()) for x in job_ids.split(",")]
        else:
            job_ids_list = list(job_ids)
        if not job_ids_list:
            raise ValueError("job_ids must contain at least one job id")
        if len(set(job_ids_list)) != len(job_ids_list):
            raise ValueError("job_ids must not contain duplicate job ids")
        requested_ids = set(job_ids_list)

        deadline = time.monotonic() + timeout
        completed_jobs = {}
        last_observed: dict[int, dict[str, Any]] = {}

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            # get_jobs is a read-only observation.  Supplying its remaining
            # budget prevents one poll from overrunning the public wait limit.
            jobs_response = self.get_jobs(job_ids_list, timeout=remaining)
            jobs = jobs_response.get("jobs", [])
            if not isinstance(jobs, list):
                raise MammothAPIError(
                    "Jobs response has an invalid 'jobs' collection.",
                    details={"protocol_error": "invalid_jobs_collection"},
                )
            observed_ids: set[int] = set()

            for job in jobs:
                if not isinstance(job, dict):
                    raise MammothAPIError(
                        "Jobs response contains an invalid job record.",
                        details={"protocol_error": "invalid_job_record"},
                    )
                job_id = job.get("id")
                status = job.get("status")
                if not isinstance(job_id, int) or isinstance(job_id, bool):
                    raise MammothAPIError(
                        "Jobs response contains a job without an integer id.",
                        details={"protocol_error": "invalid_job_id"},
                    )
                if job_id not in requested_ids:
                    raise MammothAPIError(
                        "Jobs response includes a job that was not requested.",
                        details={"protocol_error": "unexpected_job_id", "job_id": job_id},
                    )
                if job_id in observed_ids:
                    raise MammothAPIError(
                        "Jobs response includes the same job more than once.",
                        details={"protocol_error": "duplicate_job_id", "job_id": job_id},
                    )
                observed_ids.add(job_id)
                observed_phase = job.get("phase") or job.get("execution_phase") or "polling"
                if not isinstance(observed_phase, str):
                    observed_phase = "polling"
                last_observed[job_id] = safe_response_body(job)

                if status == "success":
                    completed_jobs[job_id] = job
                elif status in ["failure", "error"]:
                    error_msg = job.get("response", {}).get("error", "Job failed")
                    raise MammothJobFailedError(
                        job_id,
                        error_msg,
                        observed_job=last_observed.get(job_id),
                        phase=observed_phase,
                    )
            # A partial (including empty) server response is an observation
            # that some requested jobs remain unconfirmed, never proof that
            # the whole requested set completed.
            if requested_ids <= set(completed_jobs):
                return {"jobs": [completed_jobs[job_id] for job_id in job_ids_list]}

            time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))

        # Timeout reached — use first pending job ID for error
        pending_ids = [jid for jid in job_ids_list if jid not in completed_jobs]
        pending_id = pending_ids[0] if pending_ids else job_ids_list[0]
        timeout_phase = "polling"
        observed_pending = last_observed.get(pending_id)
        if observed_pending is not None:
            candidate_phase = observed_pending.get("phase") or observed_pending.get(
                "execution_phase"
            )
            if isinstance(candidate_phase, str):
                timeout_phase = candidate_phase
        raise MammothJobTimeoutError(
            pending_id,
            timeout,
            observed_job=observed_pending,
            phase=timeout_phase,
        )
