"""Runtime contract tests.

Red until the CLI runtime (Phase 3) and command handlers exist. They assert the
registered command tree matches the manifest and that machine output, agent
mode, discovery, and recovery contracts hold.
"""

from __future__ import annotations

import importlib

import pytest

from mammoth_cli.manifest.loader import load_commands


def _app_module():
    try:
        return importlib.import_module("mammoth_cli.app")
    except ModuleNotFoundError as exc:  # pragma: no cover - red-first guard
        pytest.fail(f"CLI runtime not implemented yet: {exc}")


def _registered_paths() -> set[str]:
    app_module = _app_module()
    getter = getattr(app_module, "registered_command_paths", None)
    if getter is None:
        pytest.fail("app.registered_command_paths is not implemented yet")
    return set(getter())


def test_every_manifest_command_is_registered() -> None:
    registered = _registered_paths()
    manifest = {r["command_path"] for r in load_commands() if r.get("disposition") != "alias"}
    missing = manifest - registered
    assert not missing, f"unregistered commands: {sorted(missing)[:20]}"


def test_command_paths_match_manifest_exactly() -> None:
    registered = _registered_paths()
    manifest = {r["command_path"] for r in load_commands() if r.get("disposition") != "alias"}
    extra = registered - manifest
    assert not extra, f"registered commands missing from manifest: {sorted(extra)[:20]}"


def test_capability_registry_matches_manifests() -> None:
    caps = importlib.import_module("mammoth_cli.commands.capability")
    listing = {entry["operation_id"] for entry in caps.capability_entries()}
    from mammoth_cli.manifest.loader import load_operations

    expected = {r["operation_id"] for r in load_operations()}
    assert listing == expected


def test_schema_registry_matches_request_models() -> None:
    schema_cmd = importlib.import_module("mammoth_cli.commands.schema")
    listing = {entry["command_id"] for entry in schema_cmd.schema_entries()}
    manifest = {r["command_id"] for r in load_commands() if r.get("disposition") != "alias"}
    assert listing == manifest


def test_every_command_supports_json_no_input() -> None:
    runner = importlib.import_module("mammoth_cli.testing").make_runner()
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        result = runner.invoke_help(record["command_path"])
        assert "--output" in result and "--no-input" in result, record["command_id"]


def test_machine_stdout_contains_data_only() -> None:
    testing = importlib.import_module("mammoth_cli.testing")
    envelope = testing.sample_success_envelope()
    assert set(envelope) == {"schema_version", "data", "meta"}
    assert testing.stdout_is_clean(envelope)


def test_agent_errors_include_executable_recovery() -> None:
    errors = importlib.import_module("mammoth_cli.errors.envelope")
    sample = errors.sample_missing_project_error()
    assert sample["error"]["recovery_commands"], "agent error must include recovery commands"
    assert sample["error"]["authorization_required"] in (True, False)


def test_agent_mode_never_prompts_or_pages() -> None:
    policy = importlib.import_module("mammoth_cli.output.policy")
    ctx = policy.resolve_policy(output="json", no_input=True, is_tty=True)
    assert ctx.prompts_disabled
    assert ctx.progress_disabled
    assert ctx.pager_disabled


def test_timeout_results_include_resumable_identity() -> None:
    errors = importlib.import_module("mammoth_cli.errors.envelope")
    sample = errors.sample_timeout_error(job_id="job-123")
    assert sample["error"]["details"].get("job_id") == "job-123"
    assert any("wait" in cmd for cmd in sample["error"]["recovery_commands"])
