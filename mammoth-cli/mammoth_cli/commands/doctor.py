"""The ``doctor`` command: a read-only environment and connectivity check.

An agent or operator runs ``mammoth doctor`` to confirm, in one deterministic
envelope, that the CLI can find credentials, resolve an endpoint, and reach the
Mammoth API. Every check reports a boolean ``ok`` plus a short detail; no secret
value is ever included. The command never mutates anything and never prompts.
"""

from __future__ import annotations

import os
import platform
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

from mammoth_cli import __version__
from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.resolver import resolve_auth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import runlog, updates
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def _safe_connection_diagnostics(error: CliError, *, debug: bool) -> dict[str, Any]:
    """Return the small, allowlisted diagnostic surface exposed by doctor.

    ``CliError.details`` may contain response bodies or backend-specific
    values because it is also used by the general error envelope.  Doctor is
    deliberately stricter: it emits only stable transport metadata and never
    copies exception text or a response body into its result.
    """
    raw = error.details if isinstance(error.details, dict) else {}
    status = raw.get("status_code")
    if isinstance(status, bool) or not isinstance(status, int):
        status = None
    exception_type = raw.get("exception_type")
    if not isinstance(exception_type, str) or exception_type not in {
        "ConnectTimeout",
        "ReadTimeout",
        "Timeout",
        "ConnectionError",
        "ProxyError",
        "SSLError",
    }:
        exception_type = None
    retry_after = raw.get("retry_after")
    if isinstance(retry_after, str):
        if len(retry_after) > 10 or not retry_after.isascii() or not retry_after.isdigit():
            retry_after = None
    elif not isinstance(retry_after, int) or isinstance(retry_after, bool) or retry_after < 0:
        retry_after = None
    request_id = error.request_id or raw.get("request_id")
    if (
        not isinstance(request_id, str)
        or len(request_id) > 128
        or not re.fullmatch(r"[A-Za-z0-9._:-]+", request_id)
    ):
        request_id = None

    if status in {429, 503}:
        reason = f"http_{status}"
        detail = f"HTTP {status} response; retry the read"
    elif exception_type in {"ConnectTimeout", "ReadTimeout", "Timeout"}:
        reason = "transport_timeout"
        detail = "transport timeout; retry the read"
    elif exception_type in {"ConnectionError", "ProxyError", "SSLError"}:
        reason = "transport_connection_error"
        detail = "transport connection error; retry the read"
    else:
        reason = error.code
        detail = f"connection check failed: {error.code}"

    result: dict[str, Any] = {"error_code": error.code, "reason": reason, "detail": detail}
    for name, value in (
        ("status_code", status),
        ("exception_type", exception_type),
        ("retry_after", retry_after),
        ("request_id", request_id),
    ):
        if value is not None:
            result[name] = value

    if debug:
        method = raw.get("method")
        if isinstance(method, str) and method.upper() in {"GET", "HEAD", "OPTIONS"}:
            result["method"] = method.upper()
        endpoint = raw.get("endpoint")
        if isinstance(endpoint, str) and len(endpoint) <= 300:
            parsed = urlsplit(endpoint)
            if (
                not parsed.query
                and not parsed.fragment
                and not parsed.username
                and not parsed.password
            ):
                result["endpoint"] = parsed.path or endpoint
        phase = raw.get("phase")
        if isinstance(phase, str) and phase in {"request", "response", "decode", "authentication"}:
            result["phase"] = phase
    return result


_PROJECT_LIMIT = 20


def _visible_projects(service: Any) -> list[dict[str, Any]]:
    """Return the projects this credential can list, or an empty list."""
    response = service.list_projects(limit=_PROJECT_LIMIT + 1)
    projects = response.get("projects", []) if isinstance(response, dict) else []
    return [p for p in projects if isinstance(p, dict)]


def _nearest_existing(path: Path) -> Path:
    """Return ``path`` or its closest existing ancestor.

    A fresh account often has no ``~/.config`` yet; the first login creates
    the whole chain, so writability is judged where creation would start.
    """
    while not path.exists() and path.parent != path:
        path = path.parent
    return path


#: ``doctor --input '{"wait": N}'``: retry a failing connection for up to N
#: seconds (capped), probing every ``_WAIT_INTERVAL`` seconds.
_WAIT_INTERVAL = 15
_WAIT_MAX = 900


def _wait_seconds(invocation: Invocation) -> float:
    document = invocation.load_input() or {}
    try:
        value = float(document.get("wait") or 0)
    except (TypeError, ValueError):
        raise CliError(
            code="invalid_argument",
            message="wait must be a number of seconds.",
            hint="mammoth doctor --input '{\"wait\": 300}'",
        ) from None
    return max(0.0, min(value, _WAIT_MAX))


def doctor(invocation: Invocation) -> HandlerResult:
    """Run environment and connectivity diagnostics.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        ``(data, meta_extra)`` where ``data`` holds the Python/CLI versions, the
        active profile, and an ordered list of check results with an overall
        ``ok`` flag.
    """
    profile_name = invocation.profile or profiles.get_selected()
    checks: list[dict[str, Any]] = []

    config_directory = profiles.config_dir()
    writable_target = _nearest_existing(config_directory)
    config_ok = os.access(writable_target, os.W_OK | os.X_OK)
    checks.append(
        _check(
            "config_directory",
            config_ok,
            (
                f"{config_directory} is writable"
                if config_ok
                else f"cannot write configuration below {writable_target}"
            ),
        )
    )

    log_directory = runlog.log_dir()
    log_target = log_directory if log_directory.exists() else log_directory.parent
    log_ok = os.access(log_target, os.W_OK | os.X_OK)
    checks.append(
        _check(
            "log_directory",
            log_ok,
            (
                f"{log_directory} is writable; run logs are kept {runlog.RETENTION_DAYS} days"
                if log_ok
                else f"cannot write run logs below {log_target}; set {runlog.LOG_DIR_ENV}"
            ),
        )
    )

    latest = updates.latest_from_pypi()
    if not updates.enabled():
        version_detail = f"{__version__} installed; update check disabled ({updates.DISABLE_ENV})"
    elif latest is None:
        version_detail = f"{__version__} installed; PyPI not reachable to compare"
    elif updates.is_newer(latest):
        version_detail = f"{__version__} installed; {latest} available: {updates.UPGRADE_COMMAND}"
    else:
        version_detail = f"{__version__} installed; latest on PyPI"
    # Informational: an older CLI still works, so the check never fails.
    checks.append(_check("cli_version", True, version_detail))

    stale_skills: list[str] = []
    try:
        from mammoth_cli.skills import installer

        installs = cast(list[dict[str, Any]], installer.list_()["installs"])
        stale_skills = [i["path"] for i in installs if i["intact"] and not i["current"]]
        skill_detail = (
            f"{len(stale_skills)} installed copy(ies) older than this CLI: "
            + ", ".join(stale_skills)
            if stale_skills
            else f"{len(installs)} installed copy(ies) current"
        )
    except Exception:  # noqa: BLE001 -- informational; never fail doctor on it
        skill_detail = "install state unreadable"
    # Informational, like cli_version: an older skill still works.
    checks.append(_check("skill", True, skill_detail))

    record = profiles.get_profile(profile_name)
    checks.append(
        _check(
            "profile",
            record is not None,
            f"profile '{profile_name}' found" if record else f"no profile '{profile_name}'",
        )
    )
    keyring_error: str | None = None
    legacy_credential = False
    try:
        stored = credentials.load_credential(profile_name)
        creds_present = stored is not None
        legacy_credential = stored is not None and stored.kind == "key_secret"
    except CliError as error:
        creds_present = False
        keyring_error = error.code
    if legacy_credential:
        creds_detail = "legacy API key + secret stored; log in again with an API token"
    else:
        creds_detail = "api token present" if creds_present else "none stored"
    checks.append(_check("credentials", creds_present, keyring_error or creds_detail))

    endpoint_detail = "unresolved"
    auth_ok = False
    try:
        auth = resolve_auth(invocation)
        endpoint_detail = auth.base_url
        auth_ok = True
    except CliError as error:
        endpoint_detail = error.code
    checks.append(_check("endpoint", auth_ok, endpoint_detail))

    connection_ok = False
    connection_detail = "not attempted"
    projects: list[dict[str, Any]] | None = None
    wait_seconds = _wait_seconds(invocation)
    if auth_ok:
        started = time.monotonic()
        retries = 0
        try:
            while True:
                try:
                    with open_service(invocation) as (service, _auth):
                        service.check_connection()
                        projects = _visible_projects(service)
                    break
                except CliError as error:
                    # A 502/504 or timeout during an outage: with ``wait``,
                    # probe again instead of failing on the first try.
                    remaining = wait_seconds - (time.monotonic() - started)
                    if not error.retryable or remaining <= 0:
                        raise
                    time.sleep(min(_WAIT_INTERVAL, remaining))
                    retries += 1
            waited = time.monotonic() - started
            connection_ok = True
            connection_detail = "authenticated request succeeded" + (
                f" after {retries} retries over {round(waited)}s" if retries else ""
            )
        except CliError as error:
            diagnostics = _safe_connection_diagnostics(error, debug=invocation.debug)
            connection_detail = diagnostics.pop("detail")
            connection_check = _check("connection", connection_ok, connection_detail)
            connection_check.update(diagnostics)
            checks.append(connection_check)
        else:
            checks.append(_check("connection", connection_ok, connection_detail))
    if not auth_ok:
        checks.append(_check("connection", connection_ok, connection_detail))

    # Authentication proves an identity, not a place to work. Report the
    # projects this credential can see and whether the selected project is
    # one of them. The API exposes no role or permission data, so write
    # access is claimed by nobody here: the first write reports it.
    selected_project = resolved_project(invocation)
    if projects is not None:
        visible_ids = [p.get("id") for p in projects]
        checks.append(
            {
                # Not a failure: a new workspace has no projects until the
                # first `project ensure`, which needs doctor to pass first.
                **_check(
                    "projects",
                    True,
                    (
                        f"{len(projects)} project(s) visible in workspace"
                        if projects
                        else "no projects visible yet; 'mammoth project ensure NAME' creates one"
                    ),
                ),
                "projects": [
                    {"id": p.get("id"), "name": p.get("name")} for p in projects[:_PROJECT_LIMIT]
                ],
                "truncated": len(projects) > _PROJECT_LIMIT,
            }
        )
        if selected_project is None:
            # Not a failure: every command accepts --project explicitly. It is
            # reported so an agent knows it still has to choose one.
            project_ok = True
            project_detail = "no project selected; pass --project per command or set one"
        elif selected_project in visible_ids:
            project_ok, project_detail = True, f"project {selected_project} is visible"
        else:
            project_ok = False
            project_detail = f"project {selected_project} is not among the visible projects"
        checks.append(
            {
                **_check("project_context", project_ok, project_detail),
                "project_id": selected_project,
                "write_access": "not verifiable from the API; the first write reports it",
            }
        )

    recommendations: list[str] = []
    if record is None or not creds_present or legacy_credential:
        login_profile = f" --profile {shlex.quote(profile_name)}" if profile_name else ""
        login_storage = " --storage file" if keyring_error else ""
        recommendations.append(f"mammoth auth login{login_profile}{login_storage}")
    elif projects == []:
        recommendations.append("mammoth project ensure 'PROJECT NAME'")
    elif selected_project is None or (
        projects is not None and selected_project not in [p.get("id") for p in projects]
    ):
        recommendations.append("mammoth project list")
        recommendations.append("mammoth context project use PROJECT_ID")
    if stale_skills:
        recommendations.append("mammoth skill update")
    if not connection_ok and auth_ok and not invocation.debug:
        debug_profile = f" --profile {shlex.quote(profile_name)}" if profile_name else ""
        recommendations.append(f"mammoth doctor --debug{debug_profile}")

    data = {
        "cli_version": __version__,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "profile": profile_name,
        "project_id": resolved_project(invocation),
        "checks": checks,
        "recommendations": recommendations,
        "ok": all(c["ok"] for c in checks),
    }
    return data, {"profile": profile_name, "project_id": resolved_project(invocation)}
