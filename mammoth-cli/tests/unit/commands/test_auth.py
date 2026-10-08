"""Bespoke `auth login|status|logout` command tests. No network is touched."""

from __future__ import annotations

import io
import json
import os
import stat
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from mammoth_cli.commands import BESPOKE
from mammoth_cli.commands import auth as auth_cmd
from mammoth_cli.context import credentials, profiles
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import make_runner

_TOKEN = "mm_" + "A" * 43


def _write_login_doc(tmp_path: Path, **fields: object) -> Path:
    """Write a permission-safe login document (owner read/write only)."""
    doc = tmp_path / "login.json"
    doc.write_text(json.dumps(fields), encoding="utf-8")
    os.chmod(doc, stat.S_IRUSR | stat.S_IWUSR)
    return doc


def _saved_login(*, server_prefix: str | None = None) -> None:
    """Persist a default profile and credentials, as a completed login would."""
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=4, server_prefix=server_prefix)
    )
    credentials.store_credentials("default", storage="file", api_token=_TOKEN)
    profiles.set_selected("default")


def test_login_from_input_no_input_succeeds(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_login_doc(
        tmp_path,
        api_token=_TOKEN,
        server_prefix="release",
    )
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--input", str(doc), "--storage", "file", "--output", "json"],
        env={},
    )
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["profile"] == "default"
    assert envelope["data"]["workspace_id"] == 4
    assert envelope["data"]["base_url"] == "https://release.mammoth.io/api/v2"
    assert "check_connection" in fake_service.calls
    # Saved for real, and never leaks the token anywhere in stdout.
    stored = credentials.load_credential("default")
    assert stored is not None and stored.api_token == _TOKEN
    assert _TOKEN not in result.stdout


def test_login_noninteractive_without_source_requires_input(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    result = runner.invoke(["auth", "login", "--output", "json", "--no-input"], env={})
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "login_input_required"


def test_login_connection_failure_leaves_state_unchanged(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.connection_ok = False
    doc = _write_login_doc(tmp_path, api_token=_TOKEN)
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--input", str(doc), "--storage", "file", "--output", "json"],
        env={},
    )
    assert result.exit_code == 4
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "authentication_failed"
    assert profiles.get_profile("default") is None
    assert credentials.load_credential("default") is None


def test_login_input_document_permission_checked(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "login.json"
    doc.write_text(
        json.dumps({"api_token": _TOKEN}),
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


def test_insecure_login_document_is_rejected_before_read(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc = tmp_path / "login.json"
    doc.write_text(
        json.dumps({"api_token": "mm_SECRET_SENTINEL"}),
        encoding="utf-8",
    )
    os.chmod(doc, 0o644)

    def fail_read(*_: object, **__: object) -> str:
        raise AssertionError("insecure login document was read")

    monkeypatch.setattr(Path, "read_text", fail_read)
    result = make_runner().invoke(
        ["auth", "login", "--input", str(doc), "--output", "json", "--no-input"], env={}
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "insecure_input_file"
    assert "SECRET_SENTINEL" not in result.output


def test_login_input_document_succeeds(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "login.json"
    doc.write_text(
        json.dumps({"api_token": _TOKEN}),
        encoding="utf-8",
    )
    os.chmod(doc, stat.S_IRUSR | stat.S_IWUSR)
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--input", str(doc), "--output", "json", "--no-input"], env={}
    )
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["workspace_id"] == 4
    assert _TOKEN not in result.stdout


def test_login_document_rejects_unknown_field(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "login.json"
    doc.write_text(
        json.dumps({"api_token": _TOKEN, "extra_field": "nope"}),
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


@pytest.mark.parametrize(
    ("name", "payload", "expected"),
    [
        (
            "duplicate.json",
            b'{"api_token":"mm_first","api_token":"mm_second"}',
            "duplicate_input_key",
        ),
        (
            "overflow.json",
            b'{"api_token":"mm_k","server_prefix":1e999}',
            "nonfinite_input_number",
        ),
    ],
)
def test_login_file_uses_strict_shared_admission(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    tmp_path: Path,
    name: str,
    payload: bytes,
    expected: str,
) -> None:
    doc = tmp_path / name
    doc.write_bytes(payload)
    os.chmod(doc, stat.S_IRUSR | stat.S_IWUSR)
    result = make_runner().invoke(
        ["auth", "login", "--input", str(doc), "--output", "json", "--no-input"],
        env={},
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == expected
    assert "check_connection" not in fake_service.calls


def test_login_stdin_uses_strict_shared_admission(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        auth_cmd.sys,
        "stdin",
        io.BytesIO(b'{"api_token":"mm_k","api_token":"mm_again"}'),
    )
    invocation = Invocation(
        command_id="auth.login",
        output="json",
        no_input=True,
        input_file="-",
        input_format="json",
    )
    with pytest.raises(CliError) as excinfo:
        auth_cmd._run_login(invocation, server_prefix=None, storage="file", method="token")
    assert excinfo.value.code == "duplicate_input_key"
    assert "check_connection" not in fake_service.calls


def test_login_prompt_path_when_interactive(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A real TTY must win over the ambient CI-like heuristic: even with CI set,
    # a genuine interactive terminal prompts rather than demanding --input.
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("TERM", "dumb")
    monkeypatch.setattr(auth_cmd.sys.stdin, "isatty", lambda: True)

    def fake_prompt(text: str, hide_input: bool = False, type: object = None) -> object:
        return _TOKEN

    monkeypatch.setattr(auth_cmd.typer, "prompt", fake_prompt)
    invocation = Invocation(command_id="auth.login", output="table", no_input=False)
    data, _meta = auth_cmd._run_login(
        invocation, server_prefix=None, storage="file", method="token"
    )
    assert data["workspace_id"] == 4
    stored = credentials.load_credential("default")
    assert stored is not None and stored.api_token == _TOKEN


def test_login_bare_prompts_for_the_token_only(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The token names its workspace: interactive login asks for the token and
    # learns the workspace from the server.
    monkeypatch.setattr(auth_cmd.sys.stdin, "isatty", lambda: True)
    asked: list[str] = []

    def fake_prompt(text: str, hide_input: bool = False, type: object = None) -> object:
        asked.append(text)
        return _TOKEN

    monkeypatch.setattr(auth_cmd.typer, "prompt", fake_prompt)
    invocation = Invocation(command_id="auth.login", output="table", no_input=False)
    data, _meta = auth_cmd._run_login(
        invocation, server_prefix=None, storage="file", method="token"
    )
    assert asked == ["API token"], asked
    assert data["workspace_id"] == 4
    assert data["credential"] == "token"


def test_login_no_tty_names_the_reason(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Without a source and without a TTY, the error must name the concrete
    # blocker (not a terminal) rather than the misleading "run in a terminal".
    monkeypatch.setattr(auth_cmd.sys.stdin, "isatty", lambda: False)
    invocation = Invocation(command_id="auth.login", output="table", no_input=False)
    with pytest.raises(CliError) as excinfo:
        auth_cmd._run_login(invocation, server_prefix=None, storage="file", method="token")
    assert excinfo.value.code == "login_input_required"
    assert "stdin is not an interactive terminal" in (excinfo.value.hint or "")


def test_logout_prompt_path_wins_over_ci(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Same rule for the logout confirmation: a real TTY confirms even under CI.
    _saved_login(server_prefix="release")
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(auth_cmd.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(auth_cmd.typer, "confirm", lambda text, default=False: True)
    invocation = Invocation(command_id="auth.logout", output="table", no_input=False)
    auth_cmd._run_logout(invocation, all_profiles=False, yes=False)
    assert credentials.load_credential("default") is None


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
    _saved_login(server_prefix="release")
    result = runner.invoke(["auth", "status", "--output", "json", "--no-input"])
    envelope = json.loads(result.stdout)
    assert envelope["data"]["has_credentials"] is True
    assert envelope["data"]["workspace_id"] == 4
    assert envelope["data"]["endpoint"] == "https://release.mammoth.io/api/v2"


def test_status_check_true_reports_connected(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    _saved_login(server_prefix="release")
    result = runner.invoke(["auth", "status", "--check", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["checked"] is True
    assert envelope["data"]["connected"] is True


def test_status_check_failure_surfaces_mapped_error(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    runner = make_runner()
    _saved_login(server_prefix="release")
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
    _saved_login(server_prefix="release")
    result = runner.invoke(["auth", "logout", "--yes", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["removed_profiles"] == ["default"]
    assert profiles.get_profile("default") is None
    assert credentials.load_credential("default") is None


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
    result = runner.invoke(["auth", "logout", "--all", "--yes", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert sorted(envelope["data"]["removed_profiles"]) == ["default", "legacy"]
    # Both profiles are gone from the store.
    assert profiles.list_profile_names() == []
    assert credentials.load_credential("default") is None
    assert credentials.load_credentials("legacy") is None


def test_logout_all_and_profile_are_mutually_exclusive(isolated_cli_config: Path) -> None:
    runner = make_runner()
    result = runner.invoke(
        ["auth", "logout", "--all", "--profile", "default", "--yes", "--output", "json"]
    )
    assert result.exit_code == 2
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_argument_combination"


def test_login_prompt_strips_whitespace_and_prints_masked_receipt(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A hidden paste often carries a trailing newline or space; that must not
    # reach the backend as part of the secret. The user gets a receipt with
    # the length and last four characters on stderr, never the value.
    monkeypatch.setattr(auth_cmd.sys.stdin, "isatty", lambda: True)

    def fake_prompt(text: str, hide_input: bool = False, type: object = None) -> object:
        if "Workspace" in text:
            return 4
        return f"  {_TOKEN}\n"

    monkeypatch.setattr(auth_cmd.typer, "prompt", fake_prompt)
    invocation = Invocation(command_id="auth.login", output="table", no_input=False)
    auth_cmd._run_login(invocation, server_prefix=None, storage="file", method="token")
    stored = credentials.load_credential("default")
    assert stored is not None and stored.api_token == _TOKEN
    err = capsys.readouterr().err
    assert "API token: 46 characters, ending in …AAAA" in err
    assert _TOKEN not in err


def test_login_prompt_rejects_empty_secret_before_any_request(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth_cmd.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(auth_cmd.typer, "prompt", lambda *a, **k: "   ")
    invocation = Invocation(command_id="auth.login", output="table", no_input=False)
    with pytest.raises(CliError) as excinfo:
        auth_cmd._run_login(invocation, server_prefix=None, storage="file", method="token")
    assert excinfo.value.code == "login_input_required"
    assert fake_service.call_log == []


def test_login_auth_failure_names_endpoint_and_masked_key(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.connection_ok = False
    token = "mm_" + "B" * 39 + "1234"
    doc = _write_login_doc(tmp_path, api_token=token)
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--input", str(doc), "--storage", "file", "--output", "json"],
        env={},
    )
    assert result.exit_code == 4
    error = json.loads(result.stderr)["error"]
    assert error["code"] == "authentication_failed"
    assert error["details"]["endpoint_base_url"] == "https://app.mammoth.io/api/v2"
    assert error["details"]["credential_receipt"] == {
        "type": "api token",
        "shape": "46 characters, ending in …1234",
    }
    assert token not in result.stderr
    assert "per environment" in error["hint"]


# --- API token (Bearer, mm_...) ------------------------------------------------


def _capture_auth(monkeypatch: pytest.MonkeyPatch, service: FakeMammothService) -> list[Any]:
    seen: list[Any] = []

    def _build(auth: Any, **_kwargs: Any) -> FakeMammothService:
        seen.append(auth)
        return service

    monkeypatch.setattr(service_factory, "build_service", _build)
    return seen


def test_login_with_api_token_from_input(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _capture_auth(monkeypatch, fake_service)
    doc = _write_login_doc(tmp_path, api_token=_TOKEN)
    result = make_runner().invoke(
        ["auth", "login", "--input", str(doc), "--storage", "file", "--output", "json"], env={}
    )
    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout)["data"]["credential"] == "token"
    assert seen[0].api_token == _TOKEN and seen[0].api_key is None
    stored = credentials.load_credential("default")
    assert stored is not None and stored.api_token == _TOKEN
    assert credentials.load_credentials("default") is None  # no legacy pair
    assert _TOKEN not in result.stdout and _TOKEN not in result.stderr
    status = make_runner().invoke(["auth", "status", "--output", "json"], env={})
    assert json.loads(status.stdout)["data"]["credential"] == "token"


def test_login_prompt_refuses_a_legacy_api_key_without_asking_for_a_secret(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth_cmd.sys.stdin, "isatty", lambda: True)
    asked: list[str] = []

    def fake_prompt(text: str, hide_input: bool = False, type: object = None) -> object:
        asked.append(text)
        return 4 if "Workspace" in text else "legacy-api-key-value"

    monkeypatch.setattr(auth_cmd.typer, "prompt", fake_prompt)
    invocation = Invocation(command_id="auth.login", output="table", no_input=False)
    with pytest.raises(CliError) as excinfo:
        auth_cmd._run_login(invocation, server_prefix=None, storage="file", method="token")
    assert excinfo.value.code == "invalid_credentials"
    assert "mm_" in excinfo.value.message
    assert asked == ["API token"]
    assert "check_connection" not in fake_service.calls


def test_login_rejects_the_token_id_pasted_as_the_token(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    tmp_path: Path,
) -> None:
    doc = _write_login_doc(tmp_path, api_token="mm_0123456789abcdef")
    result = make_runner().invoke(
        ["auth", "login", "--input", str(doc), "--storage", "file", "--output", "json"], env={}
    )
    assert result.exit_code == 2
    error = json.loads(result.stderr)["error"]
    assert error["code"] == "invalid_credentials"
    assert "id" in error["message"]
    assert "check_connection" not in fake_service.calls


@pytest.mark.parametrize(
    "fields",
    [
        {"api_token": _TOKEN, "api_key": "k", "api_secret": "s", "workspace_id": 4},
        {"api_key": "k", "api_secret": "s", "workspace_id": 4},
        {"workspace_id": 4},
    ],
)
def test_login_document_requires_an_api_token(
    isolated_cli_config: Path,
    fake_service: FakeMammothService,
    tmp_path: Path,
    fields: dict[str, Any],
) -> None:
    doc = _write_login_doc(tmp_path, **fields)
    result = make_runner().invoke(
        ["auth", "login", "--input", str(doc), "--storage", "file", "--output", "json"], env={}
    )
    assert result.exit_code == 2, result.stdout
    assert json.loads(result.stderr)["error"]["code"] == "invalid_login_document"
    assert "check_connection" not in fake_service.calls


def test_status_asks_a_legacy_key_secret_profile_to_log_in_with_a_token(
    isolated_cli_config: Path,
) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4))
    credentials.store_credentials("default", "k", "s", storage="file")
    profiles.set_selected("default")
    result = make_runner().invoke(["auth", "status", "--output", "json"], env={})
    data = json.loads(result.stdout)["data"]
    assert data["credential"] == "key_secret"
    assert "mammoth auth login" in data["recommendation"]


def test_device_flag_cannot_be_combined_with_another_method(
    isolated_cli_config: Path,
) -> None:
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--device", "--method", "token", "--output", "json", "--no-input"],
        env={},
    )
    assert result.exit_code == 2
    assert json.loads(result.stderr)["error"]["code"] == "invalid_argument_combination"


def test_device_flag_cannot_be_combined_with_input(
    isolated_cli_config: Path, tmp_path: Path
) -> None:
    doc = _write_login_doc(tmp_path, api_token=_TOKEN)
    runner = make_runner()
    result = runner.invoke(
        ["auth", "login", "--device", "--input", str(doc), "--output", "json", "--no-input"],
        env={},
    )
    assert result.exit_code == 2
    assert json.loads(result.stderr)["error"]["code"] == "invalid_argument_combination"


def test_device_login_on_a_server_without_a_cli_client_says_so(
    isolated_cli_config: Path,
) -> None:
    runner = make_runner()
    result = runner.invoke(
        [
            *("auth", "login", "--device", "--server-prefix", "nosuchenv"),
            *("--output", "json", "--no-input"),
        ],
        env={},
    )
    assert json.loads(result.stderr)["error"]["code"] == "oauth_unavailable"


def _choose_at_real_prompt(server_prefix: str | None, typed: bytes) -> tuple[str, str]:
    """Run the real menu with ``typed`` on stdin; return the choice and the menu text."""
    invocation = Invocation(command_id="auth.login", output="table", no_input=False)
    with CliRunner().isolation(input=typed, color=False) as streams:
        chosen = auth_cmd._choose_method(None, invocation, server_prefix=server_prefix, blockers=[])
        shown = streams[1].getvalue().decode()
    return chosen, shown


def test_menu_on_a_server_without_oauth_marks_browser_unavailable() -> None:
    # An environment with no OAuth client registered.
    chosen, shown = _choose_at_real_prompt("nosuchenv", b"3\n")
    assert chosen == "token"
    assert "1) Browser (OAuth)      (not yet available on nosuchenv)" in shown
    assert "2) Device code          (not yet available on nosuchenv)" in shown
    assert "3) Paste an API token" in shown


@pytest.mark.parametrize("prefix", [None, "koyal"])
def test_empty_enter_at_the_menu_picks_nothing_and_asks_again(prefix: str | None) -> None:
    chosen, _shown = _choose_at_real_prompt(prefix, b"\n\n2\n")
    assert chosen == "device"


@pytest.mark.parametrize("prefix", [None, "koyal"])
def test_only_empty_enter_at_the_menu_never_picks_a_default(prefix: str | None) -> None:
    with pytest.raises(CliError) as excinfo:
        _choose_at_real_prompt(prefix, b"\n")
    assert excinfo.value.code == "login_input_required"


def test_invalid_choice_at_the_menu_names_the_valid_ones() -> None:
    with pytest.raises(CliError) as excinfo:
        _choose_at_real_prompt("koyal", b"9\n")
    assert excinfo.value.code == "invalid_login_method"
    assert "'9' is not a valid choice; choose 1, 2 or 3" in excinfo.value.message


def test_choosing_the_browser_without_a_client_names_the_token_option() -> None:
    with pytest.raises(CliError) as excinfo:
        auth_cmd._run_oauth_login(
            Invocation(command_id="auth.login", output="table"),
            server_prefix="nosuchenv",
            storage="file",
            open_browser=False,
            interactive=True,
        )
    assert excinfo.value.code == "oauth_unavailable"
    assert "option 3" in (excinfo.value.hint or "")


def test_choose_method_stays_silent_when_not_interactive() -> None:
    invocation = Invocation(command_id="auth.login", output="table", no_input=True)
    with CliRunner().isolation(color=False) as streams:
        chosen = auth_cmd._choose_method(
            None, invocation, server_prefix=None, blockers=["--no-input was passed"]
        )
        shown = streams[1].getvalue()
    assert chosen == "token"
    assert shown == b""


def test_closed_stdin_at_the_menu_is_a_usage_error() -> None:
    with pytest.raises(CliError) as excinfo:
        _choose_at_real_prompt("koyal", b"")
    assert excinfo.value.code == "login_input_required"
    assert excinfo.value.exit_status == EXIT_USAGE
    assert "--method" in (excinfo.value.hint or "")


def test_closed_stdin_at_the_token_prompt_is_a_usage_error() -> None:
    with CliRunner().isolation(input=b"", color=False), pytest.raises(CliError) as excinfo:
        auth_cmd._prompt_secret("API token")
    assert excinfo.value.code == "login_input_required"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_login_rejects_server_and_suggests_server_prefix() -> None:
    result = make_runner().invoke(["auth", "login", "--server", "koyal", "--output", "json"])
    assert result.exit_code == EXIT_USAGE
    error = json.loads(result.output)["error"]
    assert error["code"] == "unknown_option"
    assert "--server-prefix" in error["hint"]


@pytest.mark.parametrize("command_id", sorted(BESPOKE))
def test_every_bespoke_command_rejects_an_unknown_option(command_id: str) -> None:
    path = next(r["command_path"] for r in load_commands() if r["command_id"] == command_id).split()
    result = make_runner().invoke([*path, "--bogus", "--output", "json"])
    assert result.exit_code == EXIT_USAGE, result.output
    assert json.loads(result.output)["error"]["code"] == "unknown_option"


def _drive_login_in_a_pty(prefix: str, keys: bytes, expect: bytes) -> bytes:
    """Run the real CLI on a pseudo-terminal, send ``keys`` raw, return what it printed."""
    import pty
    import select
    import sys
    import time

    pid, fd = pty.fork()
    if pid == 0:
        os.execv(
            sys.executable,
            [sys.executable, "-m", "mammoth_cli", "auth", "login", "--server-prefix", prefix],
        )
    seen = b""
    deadline = time.monotonic() + 20
    sent = False
    try:
        while time.monotonic() < deadline and expect not in seen:
            if select.select([fd], [], [], 0.2)[0]:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                seen += chunk
            if not sent and b"Choose: " in seen:
                for key in keys:
                    time.sleep(0.5)  # let the CLI switch the terminal to raw mode first
                    os.write(fd, bytes([key]))
                sent = True
    finally:
        os.close(fd)
        os.kill(pid, 9)
        os.waitpid(pid, 0)
    return seen


def test_a_single_keypress_picks_the_method_without_enter(
    isolated_cli_config: Path,
) -> None:
    seen = _drive_login_in_a_pty("koyal", b"3", b"Choose: 3 API token")
    assert b"Choose: 3 API token" in seen, seen


def test_enter_on_a_terminal_picks_nothing_and_asks_again(isolated_cli_config: Path) -> None:
    seen = _drive_login_in_a_pty("koyal", b"\r", b"Enter 1, 2 or 3.")
    assert b"Enter 1, 2 or 3." in seen, seen
    assert b"Choose: 1" not in seen and b"Choose: 3" not in seen, seen


def test_three_wrong_keys_on_a_terminal_are_a_clean_error(isolated_cli_config: Path) -> None:
    seen = _drive_login_in_a_pty("koyal", b"xxx", b"is not a valid choice; choose 1, 2 or 3")
    assert b"'x' is not a valid choice; choose 1, 2 or 3" in seen, seen


def test_a_wrong_key_then_ctrl_d_names_the_invalid_choice(isolated_cli_config: Path) -> None:
    seen = _drive_login_in_a_pty("koyal", b"9\x04", b"is not a valid choice; choose 1, 2 or 3")
    assert b"'9' is not a valid choice; choose 1, 2 or 3" in seen, seen


def test_ctrl_d_on_a_terminal_is_a_clean_error(isolated_cli_config: Path) -> None:
    seen = _drive_login_in_a_pty("koyal", b"\x04", b"No choice was entered")
    assert b"No choice was entered" in seen, seen
