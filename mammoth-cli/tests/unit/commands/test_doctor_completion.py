"""Unit tests for the local doctor and completion commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from mammoth.exceptions import MammothAPIError

from mammoth_cli.commands import completion as completion_cmd
from mammoth_cli.commands import doctor as doctor_cmd
from mammoth_cli.context import credentials, profiles
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.mapping import map_sdk_exception
from mammoth_cli.testing import login_default_profile


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_doctor_reports_no_credentials_when_unauthenticated(
    isolated_cli_config: Path,
) -> None:
    data, _meta = doctor_cmd.doctor(_inv("doctor"))
    assert data["ok"] is False
    names = {c["name"]: c["ok"] for c in data["checks"]}
    assert names["credentials"] is False
    assert names["connection"] is False
    assert "cli_version" in data
    assert data["recommendations"] == ["mammoth auth login --profile default"]


def test_doctor_missing_explicit_profile_scopes_login_recovery(
    isolated_cli_config: Path,
) -> None:
    data, _meta = doctor_cmd.doctor(_inv("doctor", profile="named"))
    assert data["profile"] == "named"
    assert data["recommendations"] == ["mammoth auth login --profile named"]


def test_doctor_connection_ok_with_fake_service(
    isolated_cli_config: Path, fake_service: object
) -> None:
    login_default_profile()
    data, _meta = doctor_cmd.doctor(_inv("doctor"))
    names = {c["name"]: c["ok"] for c in data["checks"]}
    assert names["endpoint"] is True
    assert names["connection"] is True


@pytest.mark.parametrize(
    ("error", "error_code", "extra"),
    [
        (
            MammothAPIError(
                "gateway secret should not escape",
                status_code=503,
                method="GET",
                request_id="req-503",
                retry_after="9",
                response_body={"api_secret": "do-not-leak"},
            ),
            "http_503",
            {"status_code": 503, "request_id": "req-503", "retry_after": "9"},
        ),
        (
            MammothAPIError(
                "timed out",
                details={"exception_type": "ReadTimeout"},
                method="GET",
                endpoint="https://release.mammoth.io/api/v2/projects",
                phase="request",
            ),
            "transport_timeout",
            {"exception_type": "ReadTimeout"},
        ),
    ],
)
def test_doctor_connection_diagnostics_are_typed_and_secret_safe(
    isolated_cli_config: Path,
    fake_service: object,
    error: MammothAPIError,
    error_code: str,
    extra: dict[str, object],
) -> None:
    login_default_profile()
    service = fake_service
    assert hasattr(service, "check_connection")
    service.check_connection = lambda: (_ for _ in ()).throw(map_sdk_exception(error))  # type: ignore[attr-defined]

    data, _meta = doctor_cmd.doctor(_inv("doctor"))
    connection = next(check for check in data["checks"] if check["name"] == "connection")
    assert connection["error_code"] == "retryable_error"
    assert connection["reason"] == error_code
    assert all(connection.get(key) == value for key, value in extra.items())
    assert "response_body" not in connection
    assert "do-not-leak" not in str(data)


def test_doctor_debug_adds_only_safe_request_context(
    isolated_cli_config: Path, fake_service: object
) -> None:
    login_default_profile()
    service = fake_service
    service.check_connection = lambda: (_ for _ in ()).throw(  # type: ignore[attr-defined]
        map_sdk_exception(MammothAPIError(
            "failed",
            status_code=503,
            method="GET",
            endpoint="https://release.mammoth.io/api/v2/projects",
            phase="request",
        ))
    )

    data, _meta = doctor_cmd.doctor(_inv("doctor", debug=True))
    connection = next(check for check in data["checks"] if check["name"] == "connection")
    assert connection["method"] == "GET"
    assert connection["endpoint"] == "/api/v2/projects"
    assert connection["phase"] == "request"


def test_doctor_explicit_profile_scopes_recovery_command(
    isolated_cli_config: Path, fake_service: object
) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="named", workspace_id=4))
    credentials.store_credentials("named", "k", "s", storage="file")
    service = fake_service
    service.check_connection = lambda: (_ for _ in ()).throw(  # type: ignore[attr-defined]
        map_sdk_exception(MammothAPIError("failed", status_code=503, method="GET"))
    )

    data, _meta = doctor_cmd.doctor(_inv("doctor", profile="named"))
    assert data["profile"] == "named"
    assert "--profile named" in data["recommendations"][-1]


def test_completion_show_bash() -> None:
    data, _meta = completion_cmd.completion_show(_inv("completion.show", extra_args=["bash"]))
    assert data["shell"] == "bash"
    assert "_MAMMOTH_COMPLETE=bash_source mammoth" in data["script"]


def test_completion_show_unsupported_shell_is_usage_error() -> None:
    with pytest.raises(CliError) as excinfo:
        completion_cmd.completion_show(_inv("completion.show", extra_args=["tcsh"]))
    assert excinfo.value.code == "unsupported_shell"


def test_completion_install_writes_snippet_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    first, _ = completion_cmd.completion_install(_inv("completion.install", extra_args=["bash"]))
    assert first["added"] is True
    assert Path(first["path"]).read_text(encoding="utf-8").count("_MAMMOTH_COMPLETE") == 1
    second, _ = completion_cmd.completion_install(_inv("completion.install", extra_args=["bash"]))
    assert second["added"] is False
    assert Path(second["path"]).read_text(encoding="utf-8").count("_MAMMOTH_COMPLETE") == 1
