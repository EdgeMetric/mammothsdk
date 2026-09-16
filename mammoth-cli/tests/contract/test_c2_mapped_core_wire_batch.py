"""Offline wire contracts for the nine mapped Core ETL routes (REL-193..454).

The recording transport is the oracle: no release/backend request is made.
REL-445 is intentionally excluded because it belongs to the long-protocol
workstream.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import batch, dashboard, dataset, view, view_ops
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

PROJECT, DATASET, VIEW, BATCH, CHECKPOINT, DATA_CHECK, VERSION = 3, 731, 278, 12, 7, 8, 9


def _inv(command: str, args: list[str], input_file: str | None = None, **kwargs: Any) -> Invocation:
    return Invocation(command, output="json", project=PROJECT, no_input=True,
                      extra_args=args, input_file=input_file, **kwargs)


@contextmanager
def _bind(monkeypatch: pytest.MonkeyPatch, module: Any, service: Any):
    @contextmanager
    def opened(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()
    monkeypatch.setattr(module, "open_service", opened)
    yield


def _path(api: Any) -> str:
    return api.last().path.removeprefix("/api/v2")


def test_nine_mapped_core_routes_emit_exact_scoped_wire_requests(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)

    def run(
        module: Any,
        command: str,
        args: list[str],
        payload: dict[str, Any] | None = None,
    ) -> None:
        input_file = None
        if payload is not None:
            input_file = str(tmp_path / (command.replace(".", "-") + ".json"))
            Path(input_file).write_text(json.dumps(payload), encoding="utf-8")
        with _bind(monkeypatch, module, service):
            handler = getattr(module, command.replace(".", "_").replace("-", "_"))
            handler(_inv(command, args, input_file))

    # REL-193/194: dataset-scoped batch list/get.
    run(batch, "batch.list", [str(DATASET)], {"limit": 11, "offset": 2})
    assert (_path(api), api.last().method, api.last().query) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/batches", "GET",
        {"limit": ["11"], "offset": ["2"]})
    run(batch, "batch.get", [str(DATASET), str(BATCH)])
    assert (_path(api), api.last().method) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/batches/{BATCH}", "GET")

    # REL-207/208: checkpoint list/get.
    run(view, "view.checkpoint.list", [str(VIEW)], {"dataset_id": DATASET, "status": "success"})
    assert (_path(api), api.last().method, api.last().query) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/"
        "pipeline/checkpoints",
        "GET",
        {"status": ["success"]},
    )
    run(view, "view.checkpoint.get", [str(VIEW), str(CHECKPOINT)], {"dataset_id": DATASET})
    assert (_path(api), api.last().method) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/"
        f"pipeline/checkpoints/{CHECKPOINT}",
        "GET",
    )

    # REL-210: individual data-check read.
    run(view, "view.data-check.get", [str(VIEW), str(DATA_CHECK)], {"dataset_id": DATASET})
    assert (_path(api), api.last().method) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/"
        f"pipeline/data-checks/{DATA_CHECK}",
        "GET",
    )

    # REL-216/217: pipeline version list/get.
    run(view, "view.version.list", [str(VIEW)], {"dataset_id": DATASET, "limit": 5})
    assert (_path(api), api.last().method, api.last().query) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/"
        "pipeline/versions",
        "GET",
        {"limit": ["5"]},
    )
    run(view, "view.version.get", [str(VIEW), str(VERSION)], {"dataset_id": DATASET})
    assert (_path(api), api.last().method) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/"
        f"pipeline/versions/{VERSION}",
        "GET",
    )

    # REL-454: draft command is scoped and body is literal. Submit/discard are
    # intentionally not exercised here because they require live draft-state
    # confirmation and are covered by separate recovery controls.
    run(view, "view.draft.command", [str(VIEW)], {"dataset_id": DATASET, "command": "enter"})
    assert (_path(api), api.last().method, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/draft-mode", "POST",
        {"draft_operation": "enter"})


def test_rel454_rejects_invalid_operation_and_gates_persisted_transitions(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)

    def invoke(command: str, *, yes: bool = False, confirm: str | None = None) -> None:
        payload = tmp_path / f"draft-{command}.json"
        payload.write_text(
            json.dumps({"dataset_id": DATASET, "command": command}), encoding="utf-8"
        )
        with _bind(monkeypatch, view, service):
            view.view_draft_command(
                _inv("view.draft.command", [str(VIEW)], str(payload), yes=yes, confirm=confirm)
            )

    with pytest.raises(CliError, match="must be one of"):
        invoke("status")
    assert not api.requests
    with pytest.raises(CliError, match="must be one of"):
        invoke("commit")
    assert not api.requests
    with pytest.raises(CliError, match="explicit confirmation"):
        invoke("submit")
    assert not api.requests
    with pytest.raises(CliError, match="--confirm must exactly"):
        invoke("discard", yes=True, confirm="999")
    assert not api.requests

    invoke("submit", yes=True, confirm=str(VIEW))
    assert api.last().json_body == {"draft_operation": "submit"}


def test_rel198_view_get_honors_explicit_parent(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Explicit dataset parent is forwarded without discovery."""
    service, api = real_service(project_id=PROJECT)
    payload = tmp_path / "view-get.json"
    payload.write_text(json.dumps({"dataset_id": DATASET}), encoding="utf-8")
    with _bind(monkeypatch, view_ops, service):
        view_ops.view_get(_inv("view.get", [str(VIEW)], str(payload)))
    assert (_path(api), api.last().method) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}", "GET")


def test_rel198_view_get_rejects_nonpositive_explicit_parent_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    payload = tmp_path / "view-get-invalid.json"
    payload.write_text(json.dumps({"dataset_id": 0}), encoding="utf-8")
    with _bind(monkeypatch, view_ops, service):
        with pytest.raises(CliError):
            view_ops.view_get(_inv("view.get", [str(VIEW)], str(payload)))
    assert api.requests == []


def test_rel219_file_settings_get_emits_exact_parent_wire(
    real_service: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"delimiter": ",", "has_header": True})
    with _bind(monkeypatch, dataset, service):
        dataset.dataset_file_settings(_inv("dataset.file-settings.get", [str(DATASET)]))
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/file_settings",
        "GET",
        {},
        None,
    )


def test_rel219_file_settings_get_rejects_nonpositive_dataset_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, api = real_service(project_id=PROJECT)
    with _bind(monkeypatch, dataset, service):
        with pytest.raises(CliError):
            dataset.dataset_file_settings(_inv("dataset.file-settings.get", ["0"]))
    assert api.requests == []


def test_rel456_checkpoint_create_emits_release_body_and_parent(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(201, {"id": CHECKPOINT, "sequence": 2})
    payload = tmp_path / "checkpoint.json"
    payload.write_text(
        json.dumps({
            "dataset_id": DATASET,
            "body": {"checkpoint_name": "Revenue alert", "checkpoint_type": "alert"},
        }),
        encoding="utf-8",
    )
    with _bind(monkeypatch, view, service):
        result, _ = view.view_checkpoint_create(
            _inv("view.checkpoint.create", [str(VIEW)], str(payload))
        )
    assert (_path(api), api.last().method, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/checkpoints",
        "POST",
        {"checkpoint_name": "Revenue alert", "checkpoint_type": "alert"},
    )
    assert api.last().json_body["checkpoint_name"] == "Revenue alert"
    assert result["id"] == CHECKPOINT
    assert result["sequence"] == 2


def test_rel456_checkpoint_create_rejects_missing_body_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    payload = tmp_path / "checkpoint-invalid.json"
    payload.write_text(json.dumps({"dataset_id": DATASET}), encoding="utf-8")
    with _bind(monkeypatch, view, service):
        with pytest.raises(CliError):
            view.view_checkpoint_create(_inv("view.checkpoint.create", [str(VIEW)], str(payload)))
    assert api.requests == []


def test_rel456_checkpoint_create_rejects_nonpositive_view_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    payload = tmp_path / "checkpoint-invalid-view.json"
    payload.write_text(
        json.dumps(
            {
                "dataset_id": DATASET,
                "body": {"checkpoint_name": "Revenue alert", "checkpoint_type": "alert"},
            }
        ),
        encoding="utf-8",
    )
    with _bind(monkeypatch, view, service):
        with pytest.raises(CliError):
            view.view_checkpoint_create(_inv("view.checkpoint.create", ["0"], str(payload)))
    assert api.requests == []


def test_rel456_checkpoint_create_rejects_missing_required_field_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    payload = tmp_path / "checkpoint-missing-type.json"
    payload.write_text(
        json.dumps({"dataset_id": DATASET, "body": {"checkpoint_name": "Revenue alert"}}),
        encoding="utf-8",
    )
    with _bind(monkeypatch, view, service):
        with pytest.raises(CliError):
            view.view_checkpoint_create(_inv("view.checkpoint.create", [str(VIEW)], str(payload)))
    assert api.requests == []


def test_rel081_dashboard_tags_list_emits_exact_release_route(
    real_service: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, api = real_service()
    api.default(200, {"tags": [{"id": 7, "name": "Revenue"}]})
    with _bind(monkeypatch, dashboard, service):
        dashboard.dashboard_tags_list(_inv("dashboard.tags.list", []))
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        "/dashboards/tags",
        "GET",
        {},
        None,
    )


def test_rel268_dashboard_tag_rename_emits_exact_body_and_confirmation(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    api.default(200, {"id": 7, "name": "Sales"})
    payload = tmp_path / "tag-rename.json"
    payload.write_text(json.dumps({"name": "Sales"}), encoding="utf-8")
    invocation = _inv(
        "dashboard.tags.rename", ["7"], str(payload), yes=True, confirm="7"
    )
    with _bind(monkeypatch, dashboard, service):
        dashboard.dashboard_tags_rename(invocation)
    assert (_path(api), api.last().method, api.last().json_body) == (
        "/dashboards/tags/7",
        "PATCH",
        {"name": "Sales"},
    )


def test_rel268_dashboard_tag_rename_rejects_invalid_input_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    payload = tmp_path / "tag-rename-invalid.json"
    payload.write_text(json.dumps({"name": "  "}), encoding="utf-8")
    with _bind(monkeypatch, dashboard, service):
        with pytest.raises(CliError):
            dashboard.dashboard_tags_rename(
                _inv("dashboard.tags.rename", ["0"], str(payload), yes=True, confirm="0")
            )
    assert api.requests == []


def test_rel519_dashboard_tags_set_emits_exact_body_and_confirmation(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    api.default(200, {"id": 12, "tags": []})
    payload = tmp_path / "dashboard-tags.json"
    payload.write_text(json.dumps({"tags": []}), encoding="utf-8")
    with _bind(monkeypatch, dashboard, service):
        dashboard.dashboard_tags_set(
            _inv("dashboard.tags.set", ["12"], str(payload), yes=True, confirm="12")
        )
    assert (_path(api), api.last().method, api.last().json_body) == (
        "/dashboards/12/tags", "PUT", {"tags": []}
    )


def test_rel519_dashboard_tags_set_rejects_duplicate_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    payload = tmp_path / "dashboard-tags-invalid.json"
    payload.write_text(json.dumps({"tags": ["Revenue", "Revenue"]}), encoding="utf-8")
    with _bind(monkeypatch, dashboard, service):
        with pytest.raises(CliError):
            dashboard.dashboard_tags_set(
                _inv("dashboard.tags.set", ["12"], str(payload), yes=True, confirm="12")
            )
    assert api.requests == []


@pytest.mark.parametrize("confirm", [None, "13"])
def test_rel519_dashboard_tags_set_rejects_confirmation_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, confirm: str | None
) -> None:
    service, api = real_service()
    payload = tmp_path / "dashboard-tags-confirm.json"
    payload.write_text(json.dumps({"tags": []}), encoding="utf-8")
    with _bind(monkeypatch, dashboard, service):
        with pytest.raises(CliError):
            dashboard.dashboard_tags_set(
                _inv("dashboard.tags.set", ["12"], str(payload), yes=True, confirm=confirm)
            )
    assert api.requests == []


def test_rel002_dashboard_tag_delete_emits_exact_wire_after_confirmation(
    real_service: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, api = real_service()
    api.default(204, None)
    with _bind(monkeypatch, dashboard, service):
        dashboard.dashboard_tags_delete(
            _inv("dashboard.tags.delete", ["7"], yes=True, confirm="7")
        )
    assert (_path(api), api.last().method, api.last().json_body) == (
        "/dashboards/tags/7", "DELETE", None
    )


@pytest.mark.parametrize("confirm", [None, "8"])
def test_rel002_dashboard_tag_delete_rejects_confirmation_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, confirm: str | None
) -> None:
    service, api = real_service()
    with _bind(monkeypatch, dashboard, service):
        with pytest.raises(CliError):
            dashboard.dashboard_tags_delete(
                _inv("dashboard.tags.delete", ["7"], yes=True, confirm=confirm)
            )
    assert api.requests == []


def test_rel327_dashboard_tag_merge_emits_exact_wire_after_confirmation(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    api.default(201, {"id": 456})
    payload = tmp_path / "dashboard-tag-merge.json"
    payload.write_text(json.dumps({"target_id": 456}), encoding="utf-8")
    with _bind(monkeypatch, dashboard, service):
        dashboard.dashboard_tags_merge(
            _inv("dashboard.tags.merge", ["123"], str(payload), yes=True, confirm="123")
        )
    assert (_path(api), api.last().method, api.last().json_body) == (
        "/dashboards/tags/123/merge", "POST", {"target_id": 456}
    )


@pytest.mark.parametrize("target_id", [0, 123, True])
def test_rel327_dashboard_tag_merge_rejects_invalid_target_without_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, target_id: object
) -> None:
    service, api = real_service()
    payload = tmp_path / "dashboard-tag-merge-invalid.json"
    payload.write_text(json.dumps({"target_id": target_id}), encoding="utf-8")
    with _bind(monkeypatch, dashboard, service):
        with pytest.raises(CliError):
            dashboard.dashboard_tags_merge(
                _inv("dashboard.tags.merge", ["123"], str(payload), yes=True, confirm="123")
            )
    assert api.requests == []
