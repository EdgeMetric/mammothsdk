"""Connected apps, the current workspace and workspace OAuth clients: reachable and gated."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.normalize import REDACTED, normalize
from mammoth_cli.testing import login_default_profile, make_runner

_IDS = [
    "auth.connected-apps.list",
    "auth.connected-apps.revoke",
    "workspace.current",
    "workspace.oauth-client.list",
    "workspace.oauth-client.create",
    "workspace.oauth-client.delete",
    "workspace.oauth-client.revoke-grant",
]


@pytest.mark.parametrize("command_id", _IDS)
def test_the_command_is_registered_and_reachable_from_the_cli(command_id: str) -> None:
    assert command_id in HANDLERS
    record = command_by_id(command_id)
    assert record is not None
    result = make_runner().invoke([*record["command_path"].split(), "--help"])
    assert result.exit_code == 0


@pytest.mark.parametrize(
    ("command_id", "confirmation", "mutation_class"),
    [
        ("auth.connected-apps.list", "none", "read"),
        ("auth.connected-apps.revoke", "confirm_target", "high_impact"),
        ("workspace.current", "none", "read"),
        ("workspace.oauth-client.list", "none", "read"),
        ("workspace.oauth-client.create", "yes_always", "high_impact"),
        ("workspace.oauth-client.delete", "confirm_target", "high_impact"),
        ("workspace.oauth-client.revoke-grant", "confirm_target", "high_impact"),
    ],
)
def test_the_manifest_gates_each_command_by_what_it_does(
    command_id: str, confirmation: str, mutation_class: str
) -> None:
    record = command_by_id(command_id)
    assert record is not None
    assert (record["confirmation"], record["mutation_class"]) == (confirmation, mutation_class)


def test_deleting_an_oauth_client_without_yes_stops_before_any_request(
    isolated_cli_config: Path,
) -> None:
    login_default_profile()
    result = make_runner().invoke(
        ["workspace", "oauth-client", "delete", "5", "--output", "json", "--no-input"]
    )
    assert result.exit_code != 0
    assert "confirmation_required" in result.output


def test_revoking_a_connected_app_with_the_wrong_confirm_stops_before_any_request(
    isolated_cli_config: Path,
) -> None:
    login_default_profile()
    result = make_runner().invoke(
        ["auth", "connected-apps", "revoke", "7", "--yes", "--confirm", "8", "--output", "json"]
    )
    assert result.exit_code != 0
    assert "confirmation_target_mismatch" in result.output


def test_a_created_oauth_client_secret_is_redacted_from_output() -> None:
    """The secret is returned once; the renderer must never print it."""
    assert normalize({"id": 4, "client_secret": "oc_secret_value"})["client_secret"] == REDACTED
