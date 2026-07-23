"""Fixtures for the guarded live test suite.

These tests run the real CLI in-process against a real Mammoth tenant, with
no faked transport. They are marked ``live`` and therefore deselected by the
default ``-m 'not live'`` addopts; run them explicitly with ``-m live`` once a
credentialed environment is loaded (for example ``set -a; . ./.env.plan; set
+a``). The whole suite skips cleanly when credentials are absent, so it is a
no-op in CI and offline development.

The suite is strictly read-only: it never mutates pre-existing data. Any test
that needs a write must create and delete its own disposable resource inside
the configured test project.
"""

from __future__ import annotations

import os

import pytest

from mammoth_cli.context.resolver import (
    ENV_API_KEY,
    ENV_API_SECRET,
    ENV_SERVER_PREFIX,
    ENV_WORKSPACE_ID,
)

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
    """Return the live credential environment, skipping when it is incomplete.

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


@pytest.fixture(scope="session")
def live_project(live_env: dict[str, str]) -> str:
    """Return the configured test project id, skipping when it is unset."""
    project = os.environ.get(ENV_PROJECT_ID)
    if not project:
        pytest.skip(f"{ENV_PROJECT_ID} not set; project-scoped live tests skipped")
    return project
