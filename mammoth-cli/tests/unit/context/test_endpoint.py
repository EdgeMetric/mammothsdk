"""Endpoint resolution: server-prefix mapping, validation, and conflicts."""

from __future__ import annotations

import pytest

from mammoth_cli.context.endpoint import resolve_base_url
from mammoth_cli.errors.envelope import CliError


def test_default_prefix_maps_to_app_eu() -> None:
    assert resolve_base_url(None, None) == "https://app-eu.mammoth.io/api/v2"


def test_general_prefix_maps_to_its_own_host() -> None:
    assert resolve_base_url("release", None) == "https://release.mammoth.io/api/v2"


def test_base_url_override_wins_and_is_returned_verbatim() -> None:
    assert resolve_base_url(None, "https://custom.example.com/api/v2") == (
        "https://custom.example.com/api/v2"
    )


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
        resolve_base_url(prefix, None)
    assert excinfo.value.code == "invalid_server_prefix"
    assert excinfo.value.exit_status == 2


def test_conflicting_prefix_and_base_url_is_rejected() -> None:
    with pytest.raises(CliError) as excinfo:
        resolve_base_url("app-eu", "https://custom.example.com/api/v2")
    assert excinfo.value.code == "conflicting_endpoint"
    assert excinfo.value.exit_status == 2
