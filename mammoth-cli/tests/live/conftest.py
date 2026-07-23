"""Fixtures for the guarded live test suite.

These tests run the real CLI in-process against a real Mammoth tenant, with
no faked transport. They are marked ``live`` and therefore deselected by the
default ``-m 'not live'`` addopts; run them explicitly with ``-m live`` once a
credentialed environment is loaded (for example ``set -a; . ./.env.plan; set
+a``). The whole suite skips cleanly when credentials are absent, so it is a
no-op in CI and offline development.

Authentication requires a login; there is no environment credential path. The
suite reads a developer's credentials from the variables below purely as a
convenience, then logs them into an isolated default profile so the in-process
CLI authenticates the same way a real user would.

The suite is strictly read-only: it never mutates pre-existing data. Any test
that needs a write must create and delete its own disposable resource inside
the configured test project.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Variables the live harness reads a developer's credentials from. The resolver
# never reads these; the ``_live_login`` fixture logs them into a profile.
ENV_API_KEY = "MAMMOTH_API_KEY"
ENV_API_SECRET = "MAMMOTH_API_SECRET"
ENV_WORKSPACE_ID = "MAMMOTH_WORKSPACE_ID"
ENV_SERVER_PREFIX = "MAMMOTH_SERVER_PREFIX"

# Convention for the live suite only: the resolver reads the active project
# from ``--project`` or a saved profile, never the environment, so the suite
# picks up a project id from this dedicated variable and forwards it as
# ``--project``.
ENV_PROJECT_ID = "MAMMOTH_PROJECT_ID"

_REQUIRED = (ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID)


def _missing_credentials() -> list[str]:
    """Return the required credential variables that are unset or empty."""
    return [name for name in _REQUIRED if not os.environ.get(name)]


@pytest.fixture(scope="session")
def live_env() -> dict[str, str]:
    """Return the live credentials, skipping the suite when they are incomplete.

    Includes the server prefix when set so the CLI resolves the correct
    endpoint; otherwise the CLI falls back to its default base url.
    """
    missing = _missing_credentials()
    if missing:
        pytest.skip(f"live credentials not set: {', '.join(missing)}")
    env = {name: os.environ[name] for name in _REQUIRED}
    prefix = os.environ.get(ENV_SERVER_PREFIX)
    if prefix:
        env[ENV_SERVER_PREFIX] = prefix
    return env


@pytest.fixture(autouse=True)
def _live_login(
    live_env: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Log the live credentials into an isolated default profile.

    Isolates the config directory so the login never touches a developer's real
    profiles, then saves the profile and file-backed credentials the resolver
    reads. Depends on ``live_env`` so the whole suite skips when credentials are
    absent.
    """
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_a, **_k: str(tmp_path),
    )
    from mammoth_cli.context import credentials, profiles

    prefix = live_env.get(ENV_SERVER_PREFIX)
    profiles.save_profile(
        profiles.ProfileRecord(
            name="default",
            workspace_id=int(live_env[ENV_WORKSPACE_ID]),
            server_prefix=prefix,
        )
    )
    credentials.store_credentials(
        "default", live_env[ENV_API_KEY], live_env[ENV_API_SECRET], storage="file"
    )
    profiles.set_selected("default")


@pytest.fixture(scope="session")
def live_project(live_env: dict[str, str]) -> str:
    """Return the configured test project id, skipping when it is unset."""
    project = os.environ.get(ENV_PROJECT_ID)
    if not project:
        pytest.skip(f"{ENV_PROJECT_ID} not set; project-scoped live tests skipped")
    return project
