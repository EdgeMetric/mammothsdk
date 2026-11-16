"""`auth login --method password`: a non-interactive sign-in for automation (mammothsdk#332).

The password comes only from stdin or an owner-only file, goes only into the token request, and
never reaches the output. No network is touched: the token endpoint is replaced.
"""

from __future__ import annotations

import io
import json
import os
import stat
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import auth as auth_cmd
from mammoth_cli.context import credentials, oauth, profiles
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import make_runner

_SECRET = "pw-" + "Z9" * 8
_ACCESS = "mm_" + "A" * 43
_LOGIN = ["auth", "login", "--method", "password", "--username", "ci-bot", "--storage", "file"]


def _grant() -> dict[str, object]:
    return {"access_token": _ACCESS, "refresh_token": "7." + "r" * 40, "expires_in": 3600}


@pytest.fixture
def token_endpoint(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace the token endpoint; ``forms`` records each request, ``reply`` is its answer."""
    state: dict[str, Any] = {"forms": [], "reply": (200, _grant())}

    def post(base_url: str, form: dict[str, str]) -> tuple[int, dict[str, object]]:
        state["forms"].append((base_url, dict(form)))
        return state["reply"]  # type: ignore[no-any-return]

    monkeypatch.setattr(oauth, "_post_token", post)
    monkeypatch.setattr(oauth, "client_id_for", lambda prefix: "cli-client")
    return state


def _stdin(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    monkeypatch.setattr(auth_cmd.sys, "stdin", io.StringIO(text))


def _error(result: Any) -> dict[str, Any]:
    return dict(json.loads(result.stdout)["error"])


def test_password_from_stdin_signs_in_and_stores_a_refreshable_credential(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    token_endpoint: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stdin(monkeypatch, _SECRET + "\n")
    result = make_runner().invoke(
        [*_LOGIN, "--password-stdin", "--server-prefix", "vega", "--output", "json"], env={}
    )

    assert result.exit_code == 0, result.stderr
    ((base_url, form),) = token_endpoint["forms"]
    assert base_url == "https://vega.mammoth.io/api/v2"
    assert form == {
        "grant_type": "password",
        "username": "ci-bot",
        "password": _SECRET,
        "client_id": "cli-client",
    }
    stored = credentials.load_credential("default")
    assert stored is not None and stored.oauth is not None
    assert stored.oauth.refresh == "7." + "r" * 40
    data = json.loads(result.stdout)["data"]
    assert data["credential"] == "oauth" and data["refreshes_automatically"] is True
    assert _SECRET not in result.stdout + result.stderr


def test_password_from_a_file_is_read_without_its_newline(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    token_endpoint: dict[str, Any],
    tmp_path: Path,
) -> None:
    secret_file = tmp_path / "pw"
    secret_file.write_text(_SECRET + "\n", encoding="utf-8")
    os.chmod(secret_file, stat.S_IRUSR | stat.S_IWUSR)
    result = make_runner().invoke(
        [*_LOGIN, "--password-file", str(secret_file), "--output", "json"], env={}
    )

    assert result.exit_code == 0, result.stderr
    assert token_endpoint["forms"][0][1]["password"] == _SECRET


def test_a_password_file_others_can_read_is_refused(
    isolated_cli_config: Path, token_endpoint: dict[str, Any], tmp_path: Path
) -> None:
    secret_file = tmp_path / "pw"
    secret_file.write_text(_SECRET, encoding="utf-8")
    os.chmod(secret_file, 0o644)
    result = make_runner().invoke(
        [*_LOGIN, "--password-file", str(secret_file), "--output", "json"], env={}
    )

    assert result.exit_code == 2
    assert _error(result)["code"] == "insecure_input_file"
    assert token_endpoint["forms"] == []


def test_the_password_is_never_an_argv_value(
    isolated_cli_config: Path, token_endpoint: dict[str, Any]
) -> None:
    result = make_runner().invoke([*_LOGIN, "--password", _SECRET, "--output", "json"], env={})

    assert result.exit_code == 2
    assert _error(result)["code"] == "unknown_option"
    assert _SECRET not in result.stdout + result.stderr
    assert token_endpoint["forms"] == []


def test_a_password_source_is_required_and_only_one_is_allowed(
    isolated_cli_config: Path,
    token_endpoint: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    none = make_runner().invoke([*_LOGIN, "--output", "json"], env={})
    both = make_runner().invoke(
        [*_LOGIN, "--password-stdin", "--password-file", str(tmp_path / "x"), "--output", "json"],
        env={},
    )
    _stdin(monkeypatch, "")
    empty = make_runner().invoke([*_LOGIN, "--password-stdin", "--output", "json"], env={})

    for result in (none, both, empty):
        assert result.exit_code == 2
        assert _error(result)["code"] == "login_input_required"
    assert token_endpoint["forms"] == []


def test_a_username_is_required(
    isolated_cli_config: Path, token_endpoint: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    _stdin(monkeypatch, _SECRET)
    result = make_runner().invoke(
        ["auth", "login", "--method", "password", "--password-stdin", "--output", "json"],
        env={},
    )

    assert result.exit_code == 2
    assert "--username" in _error(result)["message"]


def test_a_server_that_forbids_the_password_grant_says_so(
    isolated_cli_config: Path, token_endpoint: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    token_endpoint["reply"] = (400, {"error": "unauthorized_client"})
    _stdin(monkeypatch, _SECRET)
    result = make_runner().invoke([*_LOGIN, "--password-stdin", "--output", "json"], env={})

    error = _error(result)
    assert result.exit_code != 0
    assert error["code"] == "password_grant_not_allowed"
    assert "--device" in error["hint"]
    assert _SECRET not in result.stdout + result.stderr
    assert credentials.load_credential("default") is None


def test_wrong_credentials_are_an_authentication_failure(
    isolated_cli_config: Path, token_endpoint: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    token_endpoint["reply"] = (401, {"error": "invalid_grant"})
    _stdin(monkeypatch, _SECRET)
    result = make_runner().invoke([*_LOGIN, "--password-stdin", "--output", "json"], env={})

    assert result.exit_code != 0
    assert _error(result)["code"] == "authentication_failed"
    assert _SECRET not in result.stdout + result.stderr


def test_invalid_grant_message_carries_the_servers_description(
    isolated_cli_config: Path, token_endpoint: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    description = "This account uses 2FA; use device sign-in."
    token_endpoint["reply"] = (
        400,
        {"error": "invalid_grant", "error_description": description},
    )
    _stdin(monkeypatch, _SECRET)
    result = make_runner().invoke([*_LOGIN, "--password-stdin", "--output", "json"], env={})

    error = _error(result)
    assert error["code"] == "authentication_failed"
    assert description in error["message"]
    assert _SECRET not in result.stdout + result.stderr


def test_workspace_id_is_sent_when_given_and_omitted_otherwise(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    token_endpoint: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stdin(monkeypatch, _SECRET)
    with_ws = make_runner().invoke(
        [*_LOGIN, "--password-stdin", "--workspace", "42", "--output", "json"], env={}
    )
    _stdin(monkeypatch, _SECRET)
    without = make_runner().invoke([*_LOGIN, "--password-stdin", "--output", "json"], env={})

    assert with_ws.exit_code == 0, with_ws.stderr
    assert without.exit_code == 0, without.stderr
    assert token_endpoint["forms"][0][1]["workspace_id"] == "42"
    assert "workspace_id" not in token_endpoint["forms"][1][1]


def test_invalid_request_about_workspaces_is_a_usage_error_with_a_hint(
    isolated_cli_config: Path, token_endpoint: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    description = "Several workspaces: 3 (Sales), 9 (Ops). Pass workspace_id."
    token_endpoint["reply"] = (
        400,
        {"error": "invalid_request", "error_description": description},
    )
    _stdin(monkeypatch, _SECRET)
    result = make_runner().invoke([*_LOGIN, "--password-stdin", "--output", "json"], env={})

    error = _error(result)
    assert result.exit_code == 2
    assert error["code"] == "password_login_invalid_request"
    assert error["message"] == description
    assert error["hint"] == "Pass --workspace ID with one of the listed workspaces."
    assert _SECRET not in result.stdout + result.stderr


def test_invalid_request_without_workspaces_has_no_workspace_hint(
    isolated_cli_config: Path, token_endpoint: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    token_endpoint["reply"] = (
        400,
        {"error": "invalid_request", "error_description": "username is required"},
    )
    _stdin(monkeypatch, _SECRET)
    result = make_runner().invoke([*_LOGIN, "--password-stdin", "--output", "json"], env={})

    error = _error(result)
    assert error["code"] == "password_login_invalid_request"
    assert error["message"] == "username is required"
    assert not error.get("hint")


def test_workspace_without_the_password_method_is_refused(
    isolated_cli_config: Path, token_endpoint: dict[str, Any]
) -> None:
    result = make_runner().invoke(
        ["auth", "login", "--device", "--workspace", "5", "--output", "json"], env={}
    )

    assert result.exit_code == 2
    assert _error(result)["code"] == "invalid_argument_combination"
    assert token_endpoint["forms"] == []


def test_a_password_login_does_not_move_the_selected_profile_without_select(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    token_endpoint: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="work", workspace_id=4), select=True)
    _stdin(monkeypatch, _SECRET)
    kept = make_runner().invoke(
        [*_LOGIN, "--password-stdin", "--profile", "ci", "--output", "json"], env={}
    )
    _stdin(monkeypatch, _SECRET)
    moved = make_runner().invoke(
        [*_LOGIN, "--password-stdin", "--profile", "ci", "--select", "--output", "json"], env={}
    )

    assert json.loads(kept.stdout)["data"]["selected"] is False
    assert json.loads(kept.stdout)["data"]["active_profile"] == "work"
    assert "--profile ci --select" in json.loads(kept.stdout)["data"]["hint"]
    assert json.loads(moved.stdout)["data"]["selected"] is True
    assert json.loads(moved.stdout)["data"]["active_profile"] == "ci"
    assert profiles.get_selected() == "ci"


def test_password_options_without_the_password_method_are_refused(
    isolated_cli_config: Path, token_endpoint: dict[str, Any]
) -> None:
    result = make_runner().invoke(
        ["auth", "login", "--device", "--username", "ci-bot", "--output", "json"], env={}
    )

    assert result.exit_code == 2
    assert _error(result)["code"] == "invalid_argument_combination"


def test_global_options_before_the_command_work_for_a_password_login(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    token_endpoint: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stdin(monkeypatch, _SECRET)
    result = make_runner().invoke(
        ["--output", "json", "--profile", "ci", *_LOGIN, "--password-stdin"], env={}
    )

    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout)["data"]["profile"] == "ci"
