"""Bespoke `auth login|status|logout` command tests. No network is touched."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from mammoth_cli.commands import auth as auth_cmd
from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.resolver import (
    ENV_API_KEY,
    ENV_API_SECRET,
    ENV_SERVER_PREFIX,
    ENV_WORKSPACE_ID,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import make_runner

ENV = {
    ENV_API_KEY: "env-key-value",
    ENV_API_SECRET: "env-secret-value",
    ENV_WORKSPACE_ID: "4",
    ENV_SERVER_PREFIX: "release",
}


def test_login_from_env_no_input_succeeds(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--from-env", "--storage", "file", "--output", "json", "--no-input"],
        env=ENV,
    )
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["profile"] == "default"
    assert envelope["data"]["workspace_id"] == 4
    assert envelope["data"]["base_url"] == "https://release.mammoth.io/api/v2"
    assert "check_connection" in fake_service.calls
    # Saved for real, and never leaks the secret value anywhere in stdout.
    assert credentials.load_credentials("default") == ("env-key-value", "env-secret-value")
    assert "env-secret-value" not in result.stdout


def test_login_noninteractive_without_source_requires_from_env_or_input(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--workspace", "4", "--output", "json", "--no-input"], env={}
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "login_input_required"


def test_login_from_env_and_input_are_mutually_exclusive(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "login.json"
    doc.write_text(
        json.dumps({"api_key": "k", "api_secret": "s", "workspace_id": 4}), encoding="utf-8"
    )
    os.chmod(doc, stat.S_IRUSR | stat.S_IWUSR)
    runner = make_runner()
    result = runner.invoke(
        [
            "auth",
            "login",
            "--from-env",
            "--input",
            str(doc),
            "--output",
            "json",
            "--no-input",
        ],
        env=ENV,
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_input_mode"


def test_login_connection_failure_leaves_state_unchanged(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    fake_service.connection_ok = False
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--from-env", "--storage", "file", "--output", "json", "--no-input"],
        env=ENV,
    )
    assert result.exit_code == 4
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "authentication_failed"
    assert profiles.get_profile("default") is None
    assert credentials.load_credentials("default") is None


def test_login_input_document_permission_checked(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "login.json"
    doc.write_text(
        json.dumps({"api_key": "doc-key", "api_secret": "doc-secret", "workspace_id": 4}),
        encoding="utf-8",
    )
    os.chmod(doc, 0o644)  # world-readable: insecure
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--input", str(doc), "--output", "json", "--no-input"], env={}
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "insecure_input_file"


def test_login_input_document_succeeds(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "login.json"
    doc.write_text(
        json.dumps({"api_key": "doc-key", "api_secret": "doc-secret", "workspace_id": 7}),
        encoding="utf-8",
    )
    os.chmod(doc, stat.S_IRUSR | stat.S_IWUSR)
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--input", str(doc), "--output", "json", "--no-input"], env={}
    )
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["workspace_id"] == 7
    assert "doc-secret" not in result.stdout


def test_login_document_rejects_unknown_field(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "login.json"
    doc.write_text(
        json.dumps({"api_key": "k", "api_secret": "s", "workspace_id": 4, "extra_field": "nope"}),
        encoding="utf-8",
    )
    os.chmod(doc, stat.S_IRUSR | stat.S_IWUSR)
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--input", str(doc), "--output", "json", "--no-input"], env={}
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_login_document"


def test_login_prompt_path_when_interactive(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Force a genuinely interactive policy regardless of the ambient CI-like
    # sandbox environment this test happens to run in.
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setattr(auth_cmd.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(auth_cmd.typer, "prompt", lambda text, hide_input=False: "prompted-" + text)
    invocation = Invocation(command_id="auth.login", output="table", no_input=False)
    data, meta = auth_cmd._run_login(
        invocation, workspace=4, server_prefix=None, storage="file", from_env=False
    )
    assert data["workspace_id"] == 4
    assert credentials.load_credentials("default") == ("prompted-API key", "prompted-API secret")


def test_status_reports_no_credentials_when_never_logged_in(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["auth", "status", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["has_credentials"] is False
    assert envelope["data"]["checked"] is False


def test_status_reports_credentials_after_login(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    runner.invoke(
        ["auth", "login", "--from-env", "--storage", "file", "--output", "json", "--no-input"],
        env=ENV,
    )
    result = runner.invoke(["auth", "status", "--output", "json", "--no-input"])
    envelope = json.loads(result.stdout)
    assert envelope["data"]["has_credentials"] is True
    assert envelope["data"]["workspace_id"] == 4
    assert envelope["data"]["endpoint"] == "https://release.mammoth.io/api/v2"


def test_status_check_true_reports_connected(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    runner.invoke(
        ["auth", "login", "--from-env", "--storage", "file", "--output", "json", "--no-input"],
        env=ENV,
    )
    result = runner.invoke(["auth", "status", "--check", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["checked"] is True
    assert envelope["data"]["connected"] is True


def test_status_check_failure_surfaces_mapped_error(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    runner.invoke(
        ["auth", "login", "--from-env", "--storage", "file", "--output", "json", "--no-input"],
        env=ENV,
    )
    fake_service.connection_ok = False
    result = runner.invoke(["auth", "status", "--check", "--output", "json", "--no-input"])
    assert result.exit_code == 4
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "authentication_failed"


def test_logout_requires_yes_when_noninteractive(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["auth", "logout", "--output", "json", "--no-input"])
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "confirmation_required"


def test_logout_is_idempotent_for_missing_profile(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(["auth", "logout", "--yes", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["removed_profiles"] == []


def test_logout_removes_credentials_and_profile(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    runner.invoke(
        ["auth", "login", "--from-env", "--storage", "file", "--output", "json", "--no-input"],
        env=ENV,
    )
    result = runner.invoke(["auth", "logout", "--yes", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["removed_profiles"] == ["default"]
    assert profiles.get_profile("default") is None
    assert credentials.load_credentials("default") is None


def test_logout_all_removes_profiles_even_with_invalid_profile(
    isolated_cli_config: Path,
) -> None:
    """``--all`` must clean up every profile, including an unparseable legacy one.

    A profile carrying an unsupported legacy base_url must not block the bulk
    logout whose entire purpose is to delete it. Cleanup iterates raw profile
    names, never parsing records.
    """
    path = profiles.profiles_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "[profiles.default]\n"
        "workspace_id = 4\n"
        'server_prefix = "release"\n\n'
        "[profiles.legacy]\n"
        "workspace_id = 7\n"
        'base_url = "https://custom.example.com/api/v2"\n',
        encoding="utf-8",
    )
    credentials.store_credentials("default", "k", "s", storage="file")
    credentials.store_credentials("legacy", "k2", "s2", storage="file")

    runner = make_runner()
    result = runner.invoke(
        ["auth", "logout", "--all", "--yes", "--output", "json", "--no-input"]
    )
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert sorted(envelope["data"]["removed_profiles"]) == ["default", "legacy"]
    # Both profiles are gone from the store.
    assert profiles.list_profile_names() == []
    assert credentials.load_credentials("default") is None
    assert credentials.load_credentials("legacy") is None


def test_logout_all_and_profile_are_mutually_exclusive(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(
        ["auth", "logout", "--all", "--profile", "default", "--yes", "--output", "json"]
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_argument_combination"
