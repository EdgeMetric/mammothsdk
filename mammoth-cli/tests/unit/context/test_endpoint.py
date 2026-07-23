"""Endpoint resolution: server-prefix mapping and validation.

The CLI exposes no base-url override: a one-label server prefix (default
``app-eu``) is the only endpoint input.
"""

from __future__ import annotations

import pytest

from mammoth_cli.context.endpoint import resolve_base_url
from mammoth_cli.errors.envelope import CliError


def test_default_prefix_maps_to_app_eu() -> None:
    assert resolve_base_url(None) == "https://app-eu.mammoth.io/api/v2"


def test_general_prefix_maps_to_its_own_host() -> None:
    assert resolve_base_url("release") == "https://release.mammoth.io/api/v2"


@pytest.mark.parametrize(
    "prefix",
    [
        "https://app-eu",
        "app-eu.mammoth.io",
        "app/eu",
        "app-eu?x=1",
        "app-eu#frag",
        "app-eu:8080",
        "app eu",
        "",
        "app_eu",
    ],
)
def test_invalid_prefixes_are_rejected(prefix: str) -> None:
    with pytest.raises(CliError) as excinfo:
        resolve_base_url(prefix)
    assert excinfo.value.code == "invalid_server_prefix"
    assert excinfo.value.exit_status == 2
