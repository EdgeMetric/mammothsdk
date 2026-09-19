"""Independent S1 local/auth/discovery contract oracles.

These tests keep the expected request shapes authored here rather than
rebuilding them from the resolver under test.  They cover both structured
admission and the local filesystem/profile effects that an SDK wire oracle
cannot observe.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.commands import completion as completion_cmd
from mammoth_cli.commands import config as config_cmd
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services.command_contract import (
    LOCAL_COMMANDS,
    resolve_command_contract,
)

S1_ROUTES = (
    "auth.login",
    "auth.logout",
    "auth.status",
    "capability.find",
    "capability.get",
    "capability.list",
    "completion.install",
    "completion.show",
    "config.get",
    "config.list",
    "config.path",
    "config.set",
    "context.project.clear",
    "context.project.status",
    "context.project.use",
    "dataset.find",
    "doctor",
    "folder.find",
    "log.path",
    "log.tail",
    "project.ensure",
    "schema.find",
    "schema.get",
    "schema.list",
    "skill.install",
    "skill.list",
    "skill.path",
    "skill.uninstall",
    "skill.update",
    "upgrade",
    "version",
)

EXPECTED_FIELDS: dict[str, tuple[str, ...]] = {
    "auth.login": ("api_key", "api_secret", "workspace_id", "server_prefix"),
    "completion.install": ("shell",),
    "completion.show": ("shell",),
    "log.tail": ("days", "limit", "errors_only", "command_id", "run_id"),
    "project.ensure": ("name",),
    "skill.install": ("agents", "scope", "force"),
    "skill.path": ("agents", "scope"),
    "skill.uninstall": ("agents", "scope"),
    "skill.update": ("agents", "scope", "force"),
}


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_every_s1_route_has_a_closed_contract() -> None:
    assert LOCAL_COMMANDS == set(S1_ROUTES)
    for command_id in S1_ROUTES:
        contract = resolve_command_contract(command_id)
        assert contract is not None
        assert contract.extensibility == "closed"
        assert tuple(field.name for field in contract.accepted_fields) == EXPECTED_FIELDS.get(
            command_id, ()
        )
        assert contract.input_schema is not None
        assert contract.input_schema["additionalProperties"] is False


@pytest.mark.parametrize("command_id", S1_ROUTES)
def test_dropped_field_negative_control(command_id: str) -> None:
    """A field omitted from the authored contract cannot disappear silently."""
    with pytest.raises(CliError, match="Unknown input field"):
        validate_input_fields(command_id, {"__dropped_s1_field__": "sentinel"})


def test_bound_local_positional_and_input_values_are_independent() -> None:
    invocation = _inv(
        "completion.show",
        extra_args=["zsh"],
        input_file=None,
    )
    assert invocation.bound_input() == {"shell": "zsh"}

    invocation = _inv(
        "skill.install",
        input_file=None,
    )
    # No input is a real empty document; defaults remain handler-owned.
    assert invocation.bound_input() == {}


def test_config_contract_has_no_structured_fields_but_updates_profile_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_args, **_kwargs: str(tmp_path),
    )
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4))
    config_cmd.config_set(
        output="json",
        profile=None,
        project=None,
        timeout=None,
        job_timeout=None,
        pipeline_timeout=None,
        color="auto",
        no_input=True,
        no_progress=True,
        debug=False,
        input_file=None,
        input_format=None,
        key="project",
        value="37",
    )
    record = profiles.get_profile("default")
    assert record is not None
    assert record.project_id == 37
    assert profiles.profiles_path().is_file()


def test_completion_contract_is_verified_by_filesystem_oracle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    result, _ = completion_cmd.completion_install(_inv("completion.install", extra_args=["fish"]))
    path = Path(result["path"])
    assert path == tmp_path / ".config" / "fish" / "config.fish"
    assert path.read_text(encoding="utf-8").count("_MAMMOTH_COMPLETE") == 1
    # The second invocation is idempotent and must not duplicate the effect.
    again, _ = completion_cmd.completion_install(_inv("completion.install", extra_args=["fish"]))
    assert again["added"] is False
    assert path.read_text(encoding="utf-8").count("_MAMMOTH_COMPLETE") == 1
