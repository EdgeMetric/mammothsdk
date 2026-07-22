"""The ``doctor`` command: a read-only environment and connectivity check.

An agent or operator runs ``mammoth doctor`` to confirm, in one deterministic
envelope, that the CLI can find credentials, resolve an endpoint, and reach the
Mammoth API. Every check reports a boolean ``ok`` plus a short detail; no secret
value is ever included. The command never mutates anything and never prompts.
"""

from __future__ import annotations

import platform
import sys
from typing import Any

from mammoth_cli import __version__
from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.resolver import resolve_auth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


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

    record = profiles.get_profile(profile_name)
    checks.append(
        _check(
            "profile",
            record is not None,
            f"profile '{profile_name}' found" if record else f"no profile '{profile_name}'",
        )
    )
    checks.append(
        _check(
            "credentials",
            credentials.has_credentials(profile_name),
            "credentials present" if credentials.has_credentials(profile_name) else "none stored",
        )
    )

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
    if auth_ok:
        try:
            with open_service(invocation) as (service, _auth):
                service.check_connection()
            connection_ok = True
            connection_detail = "authenticated request succeeded"
        except CliError as error:
            connection_detail = error.code
    checks.append(_check("connection", connection_ok, connection_detail))

    data = {
        "cli_version": __version__,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "profile": profile_name,
        "project_id": resolved_project(invocation),
        "checks": checks,
        "ok": all(c["ok"] for c in checks),
    }
    return data, {"profile": profile_name, "project_id": resolved_project(invocation)}
