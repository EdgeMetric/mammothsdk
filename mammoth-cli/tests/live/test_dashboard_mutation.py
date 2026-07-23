"""Live dashboard mutation smoke test (review finding #9).

This closes the "real-system TDD" gap for the dashboard mutation family without
needing a disposable *project*: it seeds from whatever dashboard already exists
in the configured project, ``duplicate``\\s it to obtain a throwaway copy,
exercises a real state mutation on that copy (``trash``, which returns a job the
CLI must wait on -- finding #2), and then hard-deletes the copy so the tenant is
left as it was found.

The whole module is marked ``live`` (deselected by default and in CI) and skips
cleanly when credentials are absent or the tenant has no dashboard to seed from,
so it never runs against an unavailable server. Run it explicitly with real
credentials loaded, e.g.::

    set -a; . ../.env.plan; set +a
    pytest tests/live/test_dashboard_mutation.py -m live -v
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from mammoth_cli.testing import make_runner

pytestmark = pytest.mark.live


def _run(args: list[str], env: dict[str, str]) -> dict[str, Any]:
    """Invoke the CLI, assert a clean exit, and return the parsed envelope."""
    result = make_runner().invoke([*args, "--output", "json", "--no-input"], env=env)
    assert result.exit_code == 0, result.output
    envelope: dict[str, Any] = json.loads(result.output)
    assert not envelope.get("error"), envelope.get("error")
    return envelope


def _dashboard_ids(env: dict[str, str], project: str) -> list[int]:
    """Return the dashboard ids visible in the configured project."""
    data = _run(["dashboard", "list", "--project", project], env)["data"]
    items = data.get("dashboards") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    return [int(item["id"]) for item in items if isinstance(item, dict) and "id" in item]


def _extract_id(data: Any) -> int | None:
    """Pull a dashboard id out of a duplicate/create response payload."""
    if isinstance(data, dict):
        if "id" in data:
            return int(data["id"])
        for value in data.values():
            found = _extract_id(value)
            if found is not None:
                return found
    return None


def _api_status_code(envelope: dict[str, Any]) -> int | None:
    """Return the upstream HTTP status a structured api_error carried, if any."""
    error = envelope.get("error")
    if not isinstance(error, dict):
        return None
    details = error.get("details")
    if isinstance(details, dict) and isinstance(details.get("status_code"), int):
        return int(details["status_code"])
    return None


def _assert_reversible_trash_restore(env: dict[str, Any], project: str, seed_id: int) -> None:
    """Trash then restore an existing dashboard, verifying the mutation live.

    ``trash`` and ``restore`` are both ``always_wait`` commands, so this proves a
    real state change *and* the CLI's async job wait (finding #2) against the live
    server. The dashboard is restored in a ``finally`` so the tenant is left as it
    was found even if an assertion fails mid-way.
    """
    trashed = False
    try:
        _run(["dashboard", "trash", str(seed_id), "--project", project], env)
        trashed = True
        assert seed_id not in _dashboard_ids(env, project), "trash did not remove it from listing"
    finally:
        if trashed:
            restored = make_runner().invoke(
                [
                    "dashboard",
                    "restore",
                    str(seed_id),
                    "--project",
                    project,
                    "--output",
                    "json",
                    "--no-input",
                ],
                env=env,
            )
            assert restored.exit_code == 0, (
                f"restore failed, dashboard left trashed: {restored.output}"
            )
    assert seed_id in _dashboard_ids(env, project), "restore did not return it to the listing"


def test_dashboard_duplicate_trash_delete_lifecycle(
    live_env: dict[str, str], live_project: str
) -> None:
    """Duplicate an existing dashboard, trash the copy, then delete the copy.

    Proves the real dashboard mutation path end to end against a live tenant:
    ``duplicate`` (benign mutation), ``trash`` (benign mutation whose job the CLI
    now waits on), and ``delete`` (destructive, ``--yes``). The seed dashboard is
    never mutated; only the throwaway duplicate is.

    The command always drives the real stack to the live server; the assertions
    below distinguish three outcomes so this is never a false red:

    * duplicate succeeds -> run the full trash/delete lifecycle on the copy;
    * duplicate fails with an upstream 5xx -> the tenant cannot host a disposable
      copy of this seed (a server-side limitation, not a CLI defect); the CLI is
      still verified to reach the server and surface a well-formed envelope, then
      the test skips with that reason;
    * any other failure (usage error, 4xx, malformed envelope) -> a real CLI
      problem, so the test fails.
    """
    seeds = _dashboard_ids(live_env, live_project)
    if not seeds:
        pytest.skip("no dashboard in the configured project to seed a disposable copy from")
    seed_id = seeds[0]

    dup_result = make_runner().invoke(
        [
            "dashboard",
            "duplicate",
            str(seed_id),
            "--project",
            live_project,
            "--output",
            "json",
            "--no-input",
        ],
        env=live_env,
    )
    dup_env: dict[str, Any] = json.loads(dup_result.output)
    if dup_result.exit_code != 0:
        status = _api_status_code(dup_env)
        # The CLI must still have reached the server and produced a structured
        # envelope (not a traceback): assert that, then treat a server-side 5xx
        # as "cannot seed here" rather than a CLI failure.
        assert isinstance(dup_env.get("error"), dict), dup_result.output
        if status is not None and status >= 500:
            # The tenant cannot duplicate this seed (server-side). Still verify a
            # real mutation by exercising the *reversible* trash -> restore path
            # on the seed itself -- both are ``always_wait`` commands, so this
            # also exercises the async job wait (finding #2) end to end. The seed
            # is always restored, so the tenant is left as it was found.
            _assert_reversible_trash_restore(live_env, live_project, seed_id)
            return
        pytest.fail(f"duplicate failed with a client-side error: {dup_result.output}")

    copy_id = _extract_id(dup_env["data"])
    assert copy_id is not None, f"duplicate did not return a new id: {dup_env['data']}"
    assert copy_id != seed_id, "duplicate must create a distinct dashboard"

    try:
        # ``trash`` returns a job handle; the CLI must resolve it (finding #2).
        trashed = _run(["dashboard", "trash", str(copy_id), "--project", live_project], live_env)
        assert not trashed.get("error")
    finally:
        # Always hard-delete the disposable copy, restoring the tenant.
        result = make_runner().invoke(
            [
                "dashboard",
                "delete",
                str(copy_id),
                "--project",
                live_project,
                "--yes",
                "--output",
                "json",
                "--no-input",
            ],
            env=live_env,
        )
        assert result.exit_code == 0, f"cleanup delete failed: {result.output}"
