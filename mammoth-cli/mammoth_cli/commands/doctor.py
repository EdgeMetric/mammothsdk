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
from typing import Any
from urllib.parse import urlsplit

from mammoth_cli import __version__
from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.resolver import resolve_auth
from mammoth_cli.errors.envelope import CliError
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
    elif (
        not isinstance(retry_after, int)
        or isinstance(retry_after, bool)
        or retry_after < 0
    ):
        retry_after = None
    request_id = error.request_id or raw.get("request_id")
    if not isinstance(request_id, str) or len(request_id) > 128 or not re.fullmatch(
        r"[A-Za-z0-9._:-]+", request_id
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
    writable_target = config_directory if config_directory.exists() else config_directory.parent
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
            diagnostics = _safe_connection_diagnostics(error, debug=invocation.debug)
            connection_detail = diagnostics.pop("detail")
            connection_check = _check("connection", connection_ok, connection_detail)
            connection_check.update(diagnostics)
            checks.append(connection_check)
        else:
            checks.append(_check("connection", connection_ok, connection_detail))
    if not auth_ok:
        checks.append(_check("connection", connection_ok, connection_detail))

    recommendations: list[str] = []
    if record is None or not credentials.has_credentials(profile_name):
        login_profile = f" --profile {shlex.quote(profile_name)}" if profile_name else ""
        recommendations.append(f"mammoth auth login{login_profile}")
    elif resolved_project(invocation) is None:
        recommendations.append("mammoth context project use PROJECT_ID")
    if not connection_ok and auth_ok and not invocation.debug:
        debug_profile = f" --profile {shlex.quote(profile_name)}" if profile_name else ""
        recommendations.append(
            f"mammoth doctor --debug{debug_profile} --output json --no-input"
        )

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
