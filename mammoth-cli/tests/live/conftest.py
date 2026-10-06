"""Fixtures for the guarded live test suite.

These tests run the real CLI in-process against a real Mammoth tenant, with
no faked transport. They are marked ``live`` and therefore deselected by the
default ``-m 'not live'`` addopts; run them explicitly with ``-m live`` once a
credentialed environment is loaded. The whole suite skips cleanly when
credentials are absent, so it is a no-op in CI and offline development.

Authentication is the ``mm_...`` API token only (a key + secret login no longer
exists). The token is read from the file named by ``MAMMOTH_EVAL_TOKEN_FILE``
(the test identity, for example ``apitests``) and the server comes from
``MAMMOTH_SERVER_PREFIX`` (one DNS label, default ``app``; on koyal ``koyal``).
The token names its own workspace; the CLI learns it from the server.

Alternatively set ``MAMMOTH_LIVE_LOGIN_FACTORY`` to ``module:callable``
returning an :class:`~mammoth_cli.context.resolver.ExplicitLogin` carrying an
``api_token`` (for example ``api.agents.evals.world:build_login`` on a box
with a test identity). When it is set the factory wins.

Every command runs as the CLI a person runs, not as an embedded host call:
the token is logged into an isolated default profile, so file uploads and
``--input PATH`` work. The suite never touches a developer's real profiles
and never prints the token. It never mutates pre-existing data. Any test that
needs a write must create and delete its own disposable resource, in the
configured test project or in a ``scratch_project``.
"""

from __future__ import annotations

import importlib
import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from mammoth_cli.context.resolver import ExplicitLogin

# ``tests/live`` is not a package and pytest has not put it on ``sys.path`` when
# this conftest is imported, so make the sibling helper module importable.
sys.path.append(str(Path(__file__).parent))

from live_harness import LiveCli, SalesData  # noqa: E402

# The file holding the ``mm_...`` token of the test identity.
ENV_TOKEN_FILE = "MAMMOTH_EVAL_TOKEN_FILE"
# One DNS label naming the server (default ``app``).
ENV_SERVER_PREFIX = "MAMMOTH_SERVER_PREFIX"

# Convention for the live suite only: the resolver reads the active project
# from ``--project`` or a saved profile, never the environment, so the suite
# picks up a project id from this dedicated variable and forwards it as
# ``--project``.
ENV_PROJECT_ID = "MAMMOTH_PROJECT_ID"

# ``module:callable`` returning an ExplicitLogin with an ``api_token``.
ENV_LOGIN_FACTORY = "MAMMOTH_LIVE_LOGIN_FACTORY"


def _token_from_file(path_text: str) -> str:
    """Read the token file; its content is never echoed, even on an error."""
    path = Path(path_text)
    if not path.is_file():
        pytest.skip(f"{ENV_TOKEN_FILE} does not name a file")
    token = path.read_text(encoding="utf-8").strip()
    if not token.startswith("mm_"):
        pytest.skip(f"the file named by {ENV_TOKEN_FILE} does not hold an mm_ token")
    return token


@pytest.fixture(scope="session")
def login() -> ExplicitLogin:
    """The token login: the factory when set, else the token file; skips with neither."""
    factory_ref = os.environ.get(ENV_LOGIN_FACTORY)
    if factory_ref:
        module, _, name = factory_ref.partition(":")
        factory = getattr(importlib.import_module(module), name)
        made: ExplicitLogin = factory()
        return made
    token_file = os.environ.get(ENV_TOKEN_FILE)
    if not token_file:
        pytest.skip(f"live credentials not set: {ENV_TOKEN_FILE} (or {ENV_LOGIN_FACTORY})")
    return ExplicitLogin(
        api_key=None,
        api_secret=None,
        server_prefix=os.environ.get(ENV_SERVER_PREFIX),
        api_token=_token_from_file(token_file),
    )


@pytest.fixture(scope="session", autouse=True)
def live_profile(login: ExplicitLogin, tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Log the token into an isolated default profile for the whole run.

    Isolates the config directory so the login never touches a developer's real
    profiles, then saves the profile and the file-backed credential the
    resolver reads. Depends on ``login`` so the whole suite skips when
    credentials are absent.
    """
    if not login.api_token:
        pytest.skip("the live login carries no api_token; key + secret login no longer exists")
    config = tmp_path_factory.mktemp("live-config")
    patch = pytest.MonkeyPatch()
    patch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir", lambda *_a, **_k: str(config)
    )
    patch.setenv("MAMMOTH_NO_UPDATE_CHECK", "1")
    from mammoth_cli.context import credentials, profiles, resolver
    from mammoth_cli.context.endpoint import resolve_base_url

    workspace = resolver.resolve_token_workspace(
        resolve_base_url(login.server_prefix), login.api_token, None
    )
    profiles.save_profile(
        profiles.ProfileRecord(
            name="default", workspace_id=workspace, server_prefix=login.server_prefix
        )
    )
    credentials.store_credentials("default", storage="file", api_token=login.api_token)
    profiles.set_selected("default")
    try:
        yield
    finally:
        patch.undo()


@pytest.fixture(scope="session")
def live_env(live_profile: None) -> dict[str, str]:
    """Extra environment for a CLI call: none, since the isolated profile carries the login.

    Depends on ``live_profile`` so a test asking for it skips when credentials are absent.
    """
    return {}


@pytest.fixture(scope="session")
def live_project(live_env: dict[str, str]) -> str:
    """Return the configured test project id, skipping when it is unset."""
    project = os.environ.get(ENV_PROJECT_ID)
    if not project:
        pytest.skip(f"{ENV_PROJECT_ID} not set; project-scoped live tests skipped")
    return project


@pytest.fixture(scope="module")
def live_cli(live_profile: None) -> LiveCli:
    return LiveCli()


@pytest.fixture(scope="module")
def scratch_project(live_cli: LiveCli, request: pytest.FixtureRequest) -> Iterator[int]:
    """A project this module owns; deleted (with its data) at the end, even on failure."""
    stem = request.module.__name__.rsplit(".", 1)[-1].removeprefix("test_")
    name = f"uqa-live-{stem.replace('_', '-')}-{int(time.time())}"
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
