"""Contract guard: the public configuration surface is exactly the trio plus
an optional server prefix — and nothing else.

The product requirement is that a caller configures the CLI with exactly:

* an API key,
* an API secret,
* a workspace id, and
* an OPTIONAL one-label server prefix (default ``app-eu``).

Historically an expert ``base-url`` override leaked into the public surface as a
``--base-url`` option, a ``MAMMOTH_BASE_URL`` environment variable, and a
``base_url`` profile/config field. That gave callers a second, unsupported way
to point the CLI at an endpoint. This guard makes the reduced surface explicit
and fails loudly if any base-url input creeps back in.
"""

from __future__ import annotations

import dataclasses

from mammoth_cli.context import resolver
from mammoth_cli.context.profiles import ProfileRecord
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.runtime import options as go

# The exact set of environment variables the resolver may read.
_ALLOWED_ENV_VARS = {
    "MAMMOTH_API_KEY",
    "MAMMOTH_API_SECRET",
    "MAMMOTH_WORKSPACE_ID",
    "MAMMOTH_SERVER_PREFIX",
}


def test_resolver_defines_no_base_url_env_var() -> None:
    """``MAMMOTH_BASE_URL`` must not be a known resolver constant."""
    assert not hasattr(resolver, "ENV_BASE_URL")
    env_constants = {
        value
        for name, value in vars(resolver).items()
        if name.startswith("ENV_") and isinstance(value, str)
    }
    assert "MAMMOTH_BASE_URL" not in env_constants
    assert env_constants <= _ALLOWED_ENV_VARS, (
        f"resolver exposes unexpected env vars: {env_constants - _ALLOWED_ENV_VARS}"
    )


def test_explicit_login_has_no_base_url_field() -> None:
    fields = {f.name for f in dataclasses.fields(ExplicitLogin)}
    assert "base_url" not in fields
    assert fields == {"api_key", "api_secret", "workspace_id", "server_prefix"}


def test_profile_record_has_no_base_url_field() -> None:
    fields = {f.name for f in dataclasses.fields(ProfileRecord)}
    assert "base_url" not in fields
    assert fields == {"name", "workspace_id", "server_prefix", "project_id"}


def test_no_shared_base_url_option_factory() -> None:
    """The shared option catalog no longer offers a ``--base-url`` factory."""
    assert not hasattr(go, "base_url_option")


def test_generic_leaf_declares_no_base_url_option() -> None:
    """The dynamically built shared-option parameters expose no ``--base-url``."""
    from mammoth_cli.app import _SHARED_OPTION_PARAMS

    names = {param.name for param in _SHARED_OPTION_PARAMS}
    assert "base_url" not in names


def test_config_key_surface_excludes_base_url() -> None:
    """The ``config`` command family manages no ``base_url`` key."""
    from mammoth_cli.commands.config import ALL_CONFIG_KEYS

    assert "base_url" not in ALL_CONFIG_KEYS
    assert set(ALL_CONFIG_KEYS) == {
        "output",
        "timeout",
        "job_timeout",
        "pipeline_timeout",
        "server_prefix",
        "project",
    }
