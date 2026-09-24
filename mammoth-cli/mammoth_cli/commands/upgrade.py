"""The ``upgrade`` command: update the installed mammoth CLI from PyPI.

``mammoth upgrade`` upgrades the CLI in place using whatever tool installed it,
detected in order: a ``uv tool`` install, then ``pipx``, then a plain ``pip``
fallback. It never needs administrator rights and never disables TLS.

``mammoth upgrade --check`` is a read-only report of the installed version
against the latest release on PyPI; it makes no changes and needs no
confirmation. The actual upgrade is a local mutation with an external effect, so
it follows the ``prompt_or_yes`` confirmation policy: at a terminal it prompts,
and in ``--no-input`` / machine-output mode it requires ``--yes``.

The three side-effecting seams -- install-manager detection, the PyPI
latest-version lookup, and the subprocess that runs the upgrade -- are isolated
functions so tests can exercise every path without a real network request or a
real subprocess.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

import typer

from mammoth_cli import __version__
from mammoth_cli.errors.envelope import EXIT_API, EXIT_RETRYABLE, CliError
from mammoth_cli.runtime import executor
from mammoth_cli.runtime import options as go
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]

#: The distribution name on PyPI.
PACKAGE_NAME = "mammoth-cli"

#: The PyPI JSON endpoint whose ``info.version`` is the latest release.
PYPI_JSON_URL = "https://pypi.org/pypi/mammoth-cli/json"

MANAGER_UV = "uv"
MANAGER_PIPX = "pipx"
MANAGER_PIP = "pip"

# Actions reported in the ``action`` field of the result envelope.
ACTION_CHECKED = "checked"
ACTION_UPGRADED = "upgraded"
ACTION_ALREADY_CURRENT = "already_current"
ACTION_WOULD_UPGRADE = "would_upgrade"


def _tool_root(argv: list[str]) -> str | None:
    """Return the directory a tool manager keeps its venvs in, or None.

    ``uv tool dir`` / ``pipx environment --value PIPX_LOCAL_VENVS`` answer
    with one path. Returns None (rather than raising) when the manager is
    absent or the query fails, so detection can fall through.
    """
    binary = shutil.which(argv[0])
    if not binary:
        return None
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell, trusted path
            [binary, *argv[1:]],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    root = result.stdout.strip().splitlines()
    return root[0].strip() if root else None


def _runs_under(root: str | None) -> bool:
    """Whether the running interpreter's environment lives under ``root``."""
    if not root:
        return False
    prefix = os.path.realpath(sys.prefix)
    return prefix.startswith(os.path.realpath(root).rstrip("/\\") + os.sep)


def detect_manager() -> str:
    """Detect which tool manages this CLI install.

    The decision is about the *running* environment, never about what else
    is installed on the machine: a plain venv on a host that also has a
    ``uv tool`` install must be upgraded with pip in that venv, or the
    upgrade lands somewhere else and the caller keeps the old version.
    Detection order is ``uv tool`` (``sys.executable`` under a uv tools
    directory, or ``sys.prefix`` under ``uv tool dir``), then ``pipx`` (the
    same for its venvs directory), then the ``pip`` of the running interpreter.

    Returns:
        One of :data:`MANAGER_UV`, :data:`MANAGER_PIPX`, or :data:`MANAGER_PIP`.
    """
    location = (sys.executable or "").replace("\\", "/").lower()
    if "/uv/tools/" in location or "/uv/tool/" in location:
        return MANAGER_UV
    if "/pipx/venvs/" in location or "/pipx/venv/" in location:
        return MANAGER_PIPX
    if sys.prefix != sys.base_prefix:
        # Inside some virtual environment: only a manager that owns *this*
        # environment may upgrade it.
        if _runs_under(_tool_root([uv_executable(), "tool", "dir"])):
            return MANAGER_UV
        if _runs_under(_tool_root(["pipx", "environment", "--value", "PIPX_LOCAL_VENVS"])):
            return MANAGER_PIPX
    return MANAGER_PIP


def latest_version() -> str | None:
    """Return the latest ``mammoth-cli`` version published on PyPI.

    Returns:
        The version string from ``info.version``, or None when PyPI returned a
        payload without a usable version.

    Raises:
        CliError: ``pypi_unreachable`` (retryable) when PyPI cannot be reached,
            or ``pypi_response_invalid`` when the response is not the expected
            JSON shape.
    """
    # The URL is a fixed https PyPI constant, never caller-controlled.
    request = urllib.request.Request(  # noqa: S310
        PYPI_JSON_URL, headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            payload = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise CliError(
            code="pypi_unreachable",
            message="Could not reach PyPI to determine the latest version.",
            exit_status=EXIT_RETRYABLE,
            hint="Check network connectivity and retry.",
            retryable=True,
        ) from exc
    try:
        document = json.loads(payload)
        version = document["info"]["version"]
    except (ValueError, KeyError, TypeError) as exc:
        raise CliError(
            code="pypi_response_invalid",
            message="PyPI returned an unexpected response for the latest version.",
            exit_status=EXIT_API,
            hint="Retry, or upgrade manually with uv, pipx, or pip.",
        ) from exc
    return str(version) if version else None


def _installer_uv_candidates() -> list[str]:
    """Return the uv binaries ``mammoth-install.sh``/``.ps1`` keep off PATH, newest first."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", "")
        names = ("uv.exe", os.path.join("bin", "uv.exe"))
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "share"
        )
        names = ("uv", os.path.join("bin", "uv"))
    root = os.path.join(base, "mammoth-cli")
    try:
        entries = [entry for entry in os.listdir(root) if entry.startswith("uv-")]
    except OSError:
        return []

    def _key(entry: str) -> tuple[int, ...]:
        fields = entry[3:].split(".")
        return tuple(int(field) if field.isdigit() else -1 for field in fields)

    found = []
    for entry in sorted(entries, key=_key, reverse=True):
        for name in names:
            candidate = os.path.join(root, entry, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                found.append(candidate)
                break
    return found


def uv_executable() -> str:
    """Return the uv to run: the one on PATH, else the installer's own, else ``"uv"``.

    The one-line installer puts a pinned uv in the user data directory and
    leaves PATH alone, so on a fresh macOS or Linux host ``uv`` is often not
    on PATH even though uv manages this CLI.
    """
    if shutil.which("uv"):
        return "uv"
    candidates = _installer_uv_candidates()
    return candidates[0] if candidates else "uv"


def running_base_python() -> str | None:
    """Return the base interpreter this CLI runs on, when it can be found.

    A uv upgrade re-creates the tool environment; passing the interpreter the
    CLI already runs on keeps a known-good Python instead of letting uv pick
    another one (a system python3 can be a debug or pre-release build).
    """
    base = getattr(sys, "_base_executable", "") or ""
    return base if base and os.path.isfile(base) else None


def build_upgrade_command(manager: str, target_version: str | None) -> list[str]:
    """Build the argv that upgrades (or pins) the CLI for a given manager.

    Args:
        manager: One of :data:`MANAGER_UV`, :data:`MANAGER_PIPX`,
            :data:`MANAGER_PIP`.
        target_version: An exact version to install, or None to move to the
            latest release.

    Returns:
        The command argument vector to run.
    """
    spec = f"{PACKAGE_NAME}=={target_version}" if target_version else PACKAGE_NAME
    if manager == MANAGER_UV:
        uv = uv_executable()
        python = running_base_python()
        keep_python = ["--python", python] if python else []
        if target_version:
            return [uv, "tool", "install", "--force", *keep_python, spec]
        # Not `uv tool upgrade`: it keeps an install pinned with ==X.Y.Z on
        # that version. The refresh skips uv's cached index pages.
        return [
            uv,
            "tool",
            "install",
            "--force",
            "--upgrade",
            *keep_python,
            "--refresh-package",
            PACKAGE_NAME,
            "--refresh-package",
            "mammoth-io",
            PACKAGE_NAME,
        ]
    if manager == MANAGER_PIPX:
        if target_version:
            return ["pipx", "install", "--force", spec]
        return ["pipx", "upgrade", PACKAGE_NAME]
    # pip fallback: always through the running interpreter, never a bare `pip`.
    if target_version:
        return [sys.executable, "-m", "pip", "install", spec]
    return [sys.executable, "-m", "pip", "install", "--upgrade", PACKAGE_NAME]


def run_upgrade(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run the upgrade command as a subprocess, capturing its output.

    Public so the opt-in automatic upgrade (:mod:`mammoth_cli.runtime.updates`)
    goes through the same seam tests patch here.

    Raises:
        CliError: ``upgrade_failed`` when the command cannot be launched.
    """
    try:
        return subprocess.run(  # noqa: S603 - fixed argv list, no shell interpolation
            command, capture_output=True, text=True, check=False
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CliError(
            code="upgrade_failed",
            message="Could not launch the upgrade command.",
            exit_status=EXIT_API,
            hint=f"Run it manually: {' '.join(command)}",
        ) from exc


def _envelope(
    *,
    manager: str,
    current: str,
    latest: str | None,
    target: str | None,
    action: str,
    command: list[str] | None,
) -> dict[str, Any]:
    return {
        "manager": manager,
        "current_version": current,
        "latest_version": latest,
        "target_version": target,
        "action": action,
        "command": command,
    }


def perform(invocation: Invocation, *, check: bool, target_version: str | None) -> HandlerResult:
    """Report or perform a CLI upgrade.

    Args:
        invocation: The current command's resolved global options (drives the
            confirmation decision through ``--yes`` / ``--no-input`` / output
            mode).
        check: When True, report installed vs latest and make no change.
        target_version: An exact version to install, or None for the latest.

    Returns:
        ``(data, meta_extra)`` where ``data`` carries the manager, versions, the
        resolved action, and the command that ran (or None).

    Raises:
        CliError: On a PyPI lookup failure, a declined/omitted confirmation, or
            a failed upgrade subprocess.
    """
    manager = detect_manager()
    current = __version__

    if check:
        latest = latest_version()
        if latest is None:
            action = ACTION_CHECKED
        elif latest == current:
            action = ACTION_ALREADY_CURRENT
        else:
            action = ACTION_WOULD_UPGRADE
        return (
            _envelope(
                manager=manager,
                current=current,
                latest=latest,
                target=None,
                action=action,
                command=None,
            ),
            {},
        )

    # Mutation path.
    latest = None
    if target_version is None:
        latest = latest_version()
        if latest is not None and latest == current:
            return (
                _envelope(
                    manager=manager,
                    current=current,
                    latest=latest,
                    target=None,
                    action=ACTION_ALREADY_CURRENT,
                    command=None,
                ),
                {},
            )

    command = build_upgrade_command(manager, target_version)
    action_target = target_version if target_version else "the latest version"
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"upgrade {PACKAGE_NAME} to {action_target} using {manager}",
    )
    result = run_upgrade(command)
    if result.returncode != 0:
        raise CliError(
            code="upgrade_failed",
            message=f"The upgrade command exited with status {result.returncode}.",
            exit_status=EXIT_API,
            details={
                "command": command,
                "stderr": (result.stderr or "")[-4000:],
            },
            hint=f"Run it manually to see full output: {' '.join(command)}",
        )
    return (
        _envelope(
            manager=manager,
            current=current,
            latest=latest,
            target=target_version,
            action=ACTION_UPGRADED,
            command=command,
        ),
        {},
    )


def upgrade_command(
    output: str = go.output_option(),
    profile: str | None = go.profile_option(),
    project: int | None = go.project_option(),
    timeout: float | None = go.timeout_option(),
    job_timeout: float | None = go.job_timeout_option(),
    pipeline_timeout: float | None = go.pipeline_timeout_option(),
    color: str = go.color_option(),
    no_input: bool = go.no_input_option(),
    no_progress: bool = go.no_progress_option(),
    debug: bool = go.debug_option(),
    input_file: str | None = go.input_file_option(),
    input_format: str | None = go.input_format_option(),
    yes: bool = go.yes_option(),
    check: bool = typer.Option(
        False, "--check", help="Report installed vs latest version; make no changes."
    ),
    version: str | None = typer.Option(
        None,
        "--version",
        help="Upgrade to this exact version instead of the latest.",
        metavar="X.Y.Z",
    ),
) -> None:
    """Upgrade the mammoth CLI to the latest (or a specified) version from PyPI.

    Uses the tool that installed the CLI (uv tool, pipx, or pip); never needs
    admin rights. Pass --check for a read-only version report, or a --version to
    pin an exact release. The upgrade requires --yes in non-interactive mode.
    """
    invocation = go.make_invocation(
        "upgrade",
        output=output,
        profile=profile,
        project=project,
        timeout=timeout,
        job_timeout=job_timeout,
        pipeline_timeout=pipeline_timeout,
        color=color,
        no_input=no_input,
        no_progress=no_progress,
        debug=debug,
        input_file=input_file,
        input_format=input_format,
        yes=yes,
    )

    def producer() -> tuple[Any, dict[str, Any]]:
        return perform(invocation, check=check, target_version=version)

    executor.run(
        invocation.command_id,
        invocation.output,
        producer,
        agent_mode=invocation.no_input,
        invocation=invocation,
    )
