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

Alternatively set ``MAMMOTH_LIVE_LOGIN_FACTORY`` to ``module:callable``
returning an :class:`~mammoth_cli.context.resolver.ExplicitLogin` (for example
``api.agents.evals.world:build_login`` on a box with a test identity). When it
is set the factory wins: ``live_env`` needs no key/secret and ``_live_login``
does nothing. Files that create their own scratch project and data use the
``login``, ``live_cli`` and ``scratch_project`` fixtures below and run under
either path.

The suite never mutates pre-existing data. Any test that needs a write must
create and delete its own disposable resource, in the configured test project
or in a ``scratch_project``.
"""

from __future__ import annotations

import importlib
import os
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from live_harness import LiveCli, SalesData

from mammoth_cli.context.resolver import ExplicitLogin

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

# ``module:callable`` returning an ExplicitLogin; replaces the key/secret login.
ENV_LOGIN_FACTORY = "MAMMOTH_LIVE_LOGIN_FACTORY"

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
    if os.environ.get(ENV_LOGIN_FACTORY):
        return {}
    missing = _missing_credentials()
    if missing:
        pytest.skip(f"live credentials not set: {', '.join(missing)}")
    env = {name: os.environ[name] for name in _REQUIRED}
    prefix = os.environ.get(ENV_SERVER_PREFIX)
    if prefix:
        env[ENV_SERVER_PREFIX] = prefix
    return env


@pytest.fixture(autouse=True)
def _live_login(live_env: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Log the live credentials into an isolated default profile.

    Isolates the config directory so the login never touches a developer's real
    profiles, then saves the profile and file-backed credentials the resolver
    reads. Depends on ``live_env`` so the whole suite skips when credentials are
    absent. Does nothing when a login factory is configured.
    """
    if os.environ.get(ENV_LOGIN_FACTORY):
        return
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


@pytest.fixture(scope="module")
def login(live_env: dict[str, str]) -> ExplicitLogin:
    """The credentials for embedded calls: the login factory, else key/secret."""
    factory_ref = os.environ.get(ENV_LOGIN_FACTORY)
    if factory_ref:
        module, _, name = factory_ref.partition(":")
        factory = getattr(importlib.import_module(module), name)
        made: ExplicitLogin = factory()
        return made
    return ExplicitLogin(
        api_key=live_env[ENV_API_KEY],
        api_secret=live_env[ENV_API_SECRET],
        workspace_id=int(live_env[ENV_WORKSPACE_ID]),
        server_prefix=live_env.get(ENV_SERVER_PREFIX),
    )


@pytest.fixture(scope="module")
def live_cli(login: ExplicitLogin) -> LiveCli:
    return LiveCli(login)


@pytest.fixture(scope="module")
def scratch_project(live_cli: LiveCli, request: pytest.FixtureRequest) -> Iterator[int]:
    """A project this module owns; deleted (with its data) at the end, even on failure."""
    stem = request.module.__name__.rsplit(".", 1)[-1].removeprefix("test_")
    name = f"live-{stem.replace('_', '-')}-{int(time.time())}"
    data, _ = live_cli.ok("project", "create", name, "--yes")
    project = int(data["id"])
    try:
        yield project
    finally:
        removed = live_cli.run(
            *("project", "delete", str(project), "--yes", "--confirm", str(project)),
            project=None,
        )
        assert "error" not in removed, f"scratch project {project} not deleted: {removed}"


_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _sales_csv() -> str:
    regions = ("North", "South", "East", "West")
    lines = ["Region,Product,Units,Revenue,Order Date,Ship Date"]
    for n in range(60):
        region = "" if n % 15 == 14 else regions[n % 4]
        month, day = n % 12 + 1, n % 28 + 1
        lines.append(
            f"{region},P{n % 7},{n % 9 + 1},{(n * 37) % 500 + 10}.5,{month}/{day}/2024,"
            f"{day:02d} {_MONTHS[month - 1]} 2024"
        )
    return "\n".join(lines) + "\n"


@pytest.fixture(scope="module")
def sales_data(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> SalesData:
    """Upload a small sales CSV into the module's scratch project and give it a view."""
    source = tmp_path_factory.mktemp("sales") / f"sales_{int(time.time())}.csv"
    source.write_text(_sales_csv(), encoding="utf-8")
    uploaded, _ = live_cli.ok("file", "upload", str(source), "--yes", project=scratch_project)
    dataset = int(uploaded["dataset_id"])
    listed, _ = live_cli.ok("view", "list", str(dataset), project=scratch_project)
    if listed["dataviews"]:
        view = int(listed["dataviews"][0]["id"])
    else:
        created, _ = live_cli.ok("view", "create", str(dataset), "--yes", project=scratch_project)
        view = int(created["id"])
    return SalesData(project=scratch_project, dataset=dataset, view=view)
