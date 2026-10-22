"""Unit tests for the ``dashboard embed`` command family (CLI GAP, S9b/S10).

Every embed command dispatches through the generic
:func:`mammoth_cli.commands.dashboard.generated_dashboard` handler, exactly
like ``dashboard.rls.*`` and ``dashboard.swap-data``. These tests pin the
dispatch shape (exact SDK symbol + kwargs) and the confirmation policy for
the commands that require ``confirm_target``: the two credential-rotating
commands (key rotate, workspace secret rotate), plus config set (can expose
or break a live embed) and origin revoke (immediately breaks the embed on
that origin's site).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_CONFIG_GET = "mammoth.api.dashboards.DashboardsAPI.embed_config_get"
_CONFIG_SET = "mammoth.api.dashboards.DashboardsAPI.embed_config_set"
_KEY_ROTATE = "mammoth.api.dashboards.DashboardsAPI.embed_key_rotate"
_USAGE_GET = "mammoth.api.dashboards.DashboardsAPI.embed_usage_get"
_ORIGIN_REVOKE = "mammoth.api.dashboards.DashboardsAPI.embed_origin_revoke"
_PREVIEW_TOKEN_CREATE = "mammoth.api.dashboards.DashboardsAPI.embed_preview_token_create"
_SECRET_ROTATE = "mammoth.api.dashboards.DashboardsAPI.embed_secret_rotate"
_LIFETIME_SET = "mammoth.api.dashboards.DashboardsAPI.embed_lifetime_set"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write_doc(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


def test_config_get_uses_positional_dashboard_id(fake_service: FakeMammothService) -> None:
    dashboard_cmd.generated_dashboard(_inv("dashboard.embed.config.get", extra_args=["7"]))
    assert fake_service.call_log == [(_CONFIG_GET, {"dashboard_id": 7})]


def test_config_set_requires_target_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"allow_any_origin": False})
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(
            _inv("dashboard.embed.config.set", extra_args=["7"], input_file=doc)
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_config_set_dispatches_after_exact_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(
        tmp_path,
        {
            "mode": "signed",
            "allow_any_origin": False,
            "allowed_origins": ["https://intranet.example.com"],
        },
    )
    dashboard_cmd.generated_dashboard(
        _inv("dashboard.embed.config.set", extra_args=["7"], input_file=doc, yes=True, confirm="7")
    )
    assert fake_service.call_log == [
        (
            _CONFIG_SET,
            {
                "dashboard_id": 7,
                "mode": "signed",
                "allow_any_origin": False,
                "allowed_origins": ["https://intranet.example.com"],
            },
        )
    ]


def test_config_set_rejects_mismatched_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"allow_any_origin": False})
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(
            _inv(
                "dashboard.embed.config.set",
                extra_args=["7"],
                input_file=doc,
                yes=True,
                confirm="8",
            )
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_key_rotate_requires_target_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(_inv("dashboard.embed.key.rotate", extra_args=["7"]))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_key_rotate_dispatches_after_exact_confirm_target(
    fake_service: FakeMammothService,
) -> None:
    dashboard_cmd.generated_dashboard(
        _inv("dashboard.embed.key.rotate", extra_args=["7"], yes=True, confirm="7")
    )
    assert fake_service.call_log == [(_KEY_ROTATE, {"dashboard_id": 7})]


def test_key_rotate_rejects_mismatched_confirm_target(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(
            _inv("dashboard.embed.key.rotate", extra_args=["7"], yes=True, confirm="8")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_usage_get_uses_positional_dashboard_id(fake_service: FakeMammothService) -> None:
    dashboard_cmd.generated_dashboard(_inv("dashboard.embed.usage.get", extra_args=["7"]))
    assert fake_service.call_log == [(_USAGE_GET, {"dashboard_id": 7})]


def test_origin_revoke_requires_target_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"origin": "https://old.example.com"})
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(
            _inv("dashboard.embed.origin.revoke", extra_args=["7"], input_file=doc)
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_origin_revoke_dispatches_after_exact_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"origin": "https://old.example.com"})
    dashboard_cmd.generated_dashboard(
        _inv(
            "dashboard.embed.origin.revoke",
            extra_args=["7"],
            input_file=doc,
            yes=True,
            confirm="7",
        )
    )
    assert fake_service.call_log == [
        (_ORIGIN_REVOKE, {"dashboard_id": 7, "origin": "https://old.example.com"})
    ]


def test_origin_revoke_rejects_mismatched_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"origin": "https://old.example.com"})
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(
            _inv(
                "dashboard.embed.origin.revoke",
                extra_args=["7"],
                input_file=doc,
                yes=True,
                confirm="8",
            )
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_preview_token_create_forwards_claims(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"claims": {"region": ["East"]}})
    dashboard_cmd.generated_dashboard(
        _inv("dashboard.embed.preview-token.create", extra_args=["7"], input_file=doc)
    )
    assert fake_service.call_log == [
        (_PREVIEW_TOKEN_CREATE, {"dashboard_id": 7, "claims": {"region": ["East"]}})
    ]


def test_secret_rotate_requires_target_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(_inv("dashboard.embed.secret.rotate", extra_args=["42"]))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_secret_rotate_dispatches_after_exact_confirm_target(
    fake_service: FakeMammothService,
) -> None:
    dashboard_cmd.generated_dashboard(
        _inv("dashboard.embed.secret.rotate", extra_args=["42"], yes=True, confirm="42")
    )
    assert fake_service.call_log == [(_SECRET_ROTATE, {"workspace_id": 42})]


def test_lifetime_set_forwards_token_ttl_no_confirmation_needed(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"token_ttl": 900})
    dashboard_cmd.generated_dashboard(
        _inv("dashboard.embed.lifetime.set", extra_args=["42"], input_file=doc)
    )
    assert fake_service.call_log == [(_LIFETIME_SET, {"workspace_id": 42, "token_ttl": 900})]


_ROTATED = {"secret": "whsec-new-signing-secret", "token_ttl": 300}


def test_secret_rotate_masks_the_new_secret_by_default(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_SECRET_ROTATE] = dict(_ROTATED)
    result = make_runner().invoke(
        ["dashboard", "embed", "secret", "rotate", "42", "--yes", "--confirm", "42"]
        + ["--output", "json"],
    )
    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout)["data"]["secret"] == "***REDACTED***"
    assert _ROTATED["secret"] not in result.stdout


def test_secret_rotate_reveal_prints_the_new_secret(fake_service: FakeMammothService) -> None:
    # #278: the API shows the signing secret once; masked, the rotation was unusable.
    fake_service.responses[_SECRET_ROTATE] = dict(_ROTATED)
    result = make_runner().invoke(
        ["dashboard", "embed", "secret", "rotate", "42", "--yes", "--confirm", "42"]
        + ["--reveal", "--output", "json"],
    )
    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout)["data"]["secret"] == _ROTATED["secret"]


def test_preview_token_create_reveal_prints_the_token(fake_service: FakeMammothService) -> None:
    fake_service.responses[_PREVIEW_TOKEN_CREATE] = {"token": "preview-token-value"}
    result = make_runner().invoke(
        ["dashboard", "embed", "preview-token", "create", "7", "--reveal", "--output", "json"],
    )
    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout)["data"]["token"] == "preview-token-value"


def test_reveal_is_refused_on_a_command_without_a_credential(
    fake_service: FakeMammothService,
) -> None:
    result = make_runner().invoke(
        ["dashboard", "embed", "config", "get", "7", "--reveal", "--output", "json"],
    )
    assert result.exit_code != 0
    assert fake_service.call_log == []


def test_config_get_shows_has_signing_secret_as_a_boolean(
    fake_service: FakeMammothService,
) -> None:
    # #278: the boolean was rendered as "***REDACTED***" (its key ends in "secret").
    fake_service.responses[_CONFIG_GET] = {"has_signing_secret": True, "access_key": "ak-1"}
    result = make_runner().invoke(["dashboard", "embed", "config", "get", "7", "--output", "json"])
    assert result.exit_code == 0, result.stderr
    data = json.loads(result.stdout)["data"]
    assert data["has_signing_secret"] is True
    assert data["access_key"] == "***REDACTED***"


def test_lifetime_set_dry_run_refuses_a_ttl_out_of_range(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # #283: the documented example (token_ttl 1) passed --dry-run, then the real call failed.
    doc = _write_doc(tmp_path, {"token_ttl": 1})
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(
            _inv("dashboard.embed.lifetime.set", extra_args=["42"], input_file=doc, dry_run=True)
        )
    assert "between 60 and 3600" in excinfo.value.message
    assert fake_service.call_log == []
