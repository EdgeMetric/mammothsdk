"""Independent contract controls for C2/S2 project-data acquisition routes.

These tests deliberately keep the expected route inventory and representative
wire values outside the resolver implementation.  The existing family unit
tests exercise each handler; this file adds the migration-level controls:
every declared S2 route is closed, every structured value is admitted through
the shared binding boundary, and an unknown field is rejected before a service
can be opened.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import (
    addon as addon_cmd,
)
from mammoth_cli.commands import (
    annotation as annotation_cmd,
)
from mammoth_cli.commands import (
    browse as browse_cmd,
)
from mammoth_cli.commands import (
    dataset as dataset_cmd,
)
from mammoth_cli.commands import (
    file as file_cmd,
)
from mammoth_cli.commands import (
    folder as folder_cmd,
)
from mammoth_cli.commands import (
    notification as notification_cmd,
)
from mammoth_cli.commands import (
    project as project_cmd,
)
from mammoth_cli.commands import (
    trash as trash_cmd,
)
from mammoth_cli.commands import (
    workspace as workspace_cmd,
)
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.command_contract import (
    S2_COMMANDS,
    bind_command_inputs,
    resolve_command_contract,
)
from mammoth_cli.services.testing import FakeMammothService

S2_ROUTE_INVENTORY = frozenset(
    {
        "addon.connector.add",
        "addon.connector.remove",
        "addon.list",
        "addon.storage.add",
        "addon.storage.remove",
        "addon.user.add",
        "addon.user.remove",
        "annotation.comment.add",
        "annotation.create",
        "annotation.delete",
        "annotation.list",
        "annotation.update",
        "browse.folder",
        "browse.project",
        "browse.root",
        "browse.workspace",
        "dataset.bulk-delete",
        "dataset.bulk-update",
        "dataset.create",
        "dataset.create-from-pdf",
        "dataset.data",
        "dataset.delete",
        "dataset.file-settings.get",
        "dataset.file-settings.undo",
        "dataset.file-settings.update",
        "dataset.get",
        "dataset.list",
        "dataset.rename",
        "dataset.restore",
        "dataset.trash",
        "dataset.update",
        "file.bulk-delete",
        "file.delete",
        "file.extract-sheets",
        "file.get",
        "file.list",
        "file.set-password",
        "file.update",
        "file.upload",
        "file.upload-folder",
        "folder.bulk-delete",
        "folder.create",
        "folder.delete",
        "folder.get",
        "folder.list",
        "folder.move",
        "folder.root",
        "folder.trash",
        "folder.update",
        "notification.delete",
        "notification.delete-batch",
        "notification.list",
        "notification.update",
        "notification.update-batch",
        "project.bulk-delete",
        "project.bulk-update",
        "project.checkpoint.list",
        "project.create",
        "project.data-check.list",
        "project.delete",
        "project.get",
        "project.list",
        "project.pending-changes",
        "project.publish-credentials",
        "project.resource-dependencies",
        "project.resource-status",
        "project.sample-flow",
        "project.update",
        "project.user.add",
        "project.user.remove",
        "project.user.update",
        "trash.add",
        "trash.list",
        "trash.restore",
        "workspace.accept-invite",
        "workspace.app-usage",
        "workspace.check-expression",
        "workspace.create",
        "workspace.delete",
        "workspace.get",
        "workspace.list",
        "workspace.llm-task",
        "workspace.reactivate",
        "workspace.segment.list",
        "workspace.segment.update",
        "workspace.storage-breakdown",
        "workspace.update",
        "workspace.user.add",
        "workspace.user.get",
        "workspace.user.list",
        "workspace.user.remove",
        "workspace.user.remove-batch",
        "workspace.user.update",
        "workspace.user.update-batch",
    }
)


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Use the standard isolated fake profile for handler-level oracles."""
    from mammoth_cli.testing import login_default_profile

    login_default_profile()


@pytest.fixture
def isolated_cli_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Keep profile/config writes inside the test's temporary directory."""
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_args, **_kwargs: str(tmp_path),
    )
    return tmp_path


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    service = FakeMammothService()

    def _build(_auth: object, **_kwargs: object) -> FakeMammothService:
        return service

    monkeypatch.setattr(service_factory, "build_service", _build)
    return service


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, value: object) -> str:
    path = tmp_path / "s2-input.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return str(path)


def test_inventory_is_exactly_the_closed_s2_surface() -> None:
    assert S2_COMMANDS == S2_ROUTE_INVENTORY
    assert len(S2_ROUTE_INVENTORY) == 94
    for command_id in sorted(S2_ROUTE_INVENTORY):
        record = command_by_id(command_id)
        assert record is not None
        assert command_id in HANDLERS
        contract = resolve_command_contract(command_id)
        assert contract is not None
        assert contract.extensibility == "closed"
        assert contract.input_schema is not None


def test_unknown_s2_field_is_rejected_before_service_dispatch(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A dropped/misspelled field cannot reach a handler or mutate state."""
    with pytest.raises(CliError) as error:
        project_cmd.project_list(
            _inv("project.list", input_file=_write(tmp_path, {"limit": 913, "dropped": "x"}))
        )
    assert error.value.code == "unknown_input_field"
    assert fake_service.call_log == []


def test_project_positional_alias_has_an_explicit_sdk_destination() -> None:
    """The project locator must not be silently dropped or sent as project_id."""
    assert bind_command_inputs("project.get", {}, project_id=991) == {"project": 991}


@pytest.mark.parametrize(
    ("handler", "command_id", "payload", "expected_symbol", "expected_kwargs", "extra_args"),
    [
        (
            project_cmd.project_list,
            "project.list",
            {"limit": 913},
            "mammoth.api.projects.ProjectsAPI.list",
            {"limit": 913},
            [],
        ),
        (
            dataset_cmd.dataset_list,
            "dataset.list",
            {"limit": 917, "offset": 918, "sort": "S2-DATASET-SORT"},
            "mammoth.api.datasets.DatasetsAPI.list",
            {"project_id": 42, "limit": 917, "offset": 918, "sort": "S2-DATASET-SORT"},
            [],
        ),
        (
            file_cmd.file_upload,
            "file.upload",
            {
                "files": ["s2-input.csv"],
                "folder_resource_id": "S2-FOLDER",
                "append_to_ds_id": 731,
                "override_target_schema": True,
                "wait_for_completion": False,
                "timeout": 47,
            },
            "mammoth.api.files.FilesAPI.upload",
            {
                "files": ["s2-input.csv"],
                "folder_resource_id": "S2-FOLDER",
                "append_to_ds_id": 731,
                "override_target_schema": True,
                "wait_for_completion": False,
                "timeout": 47,
            },
            [],
        ),
        (
            folder_cmd.folder_list,
            "folder.list",
            {"fields": "S2-FIELDS", "limit": 919, "sort": "S2-SORT"},
            "mammoth.api.folders.FoldersAPI.list",
            {"project_id": 42, "fields": "S2-FIELDS", "limit": 919, "sort": "S2-SORT"},
            [],
        ),
        (
            browse_cmd.browse_root,
            "browse.root",
            {"name": "S2-BROWSE", "limit": 923, "include_hidden": True},
            "mammoth.api.browse.BrowseAPI.root",
            {"name": "S2-BROWSE", "limit": 923, "include_hidden": True},
            [],
        ),
        (
            addon_cmd.addon_storage_add,
            "addon.storage.add",
            {"additional_storage_gb": 929},
            "mammoth.api.addons.AddonsAPI.add_storage",
            {"additional_storage_gb": 929},
            [],
        ),
        (
            trash_cmd.trash_list,
            "trash.list",
            {"type": "S2-TRASH", "limit": 931, "folder_root": "S2-ROOT"},
            "mammoth.api.trash.TrashAPI.list",
            {"project_id": 42, "type": "S2-TRASH", "limit": 931, "folder_root": "S2-ROOT"},
            [],
        ),
        (
            notification_cmd.notification_list,
            "notification.list",
            {"status": "S2-STATUS", "is_read": False, "limit": 937},
            "mammoth.api.notifications.NotificationsAPI.list",
            {"project_id": 42, "status": "S2-STATUS", "is_read": False, "limit": 937},
            [],
        ),
        (
            annotation_cmd.annotation_create,
            "annotation.create",
            {"target_type": "S2-TARGET", "target_id": 941, "body": "S2-BODY"},
            "mammoth.api.annotations.AnnotationsAPI.create",
            {"target_type": "S2-TARGET", "target_id": 941, "body": "S2-BODY", "project_id": 42},
            [],
        ),
        (
            workspace_cmd.workspace_llm_task,
            "workspace.llm-task",
            {"task_type": "S2-TASK", "params": {"sentinel": "S2"}},
            "mammoth.api.workspaces.WorkspacesAPI.llm_task",
            {"task_type": "S2-TASK", "params": {"sentinel": "S2"}},
            [],
        ),
    ],
)
def test_representative_s2_fields_are_forwarded(
    fake_service: FakeMammothService,
    tmp_path: Path,
    handler: object,
    command_id: str,
    payload: dict[str, object],
    expected_symbol: str,
    expected_kwargs: dict[str, object],
    extra_args: list[str],
) -> None:
    # The fixture uses each family's public handler, but expected kwargs are
    # authored here rather than obtained from the resolver under test.
    handler(  # type: ignore[operator]
        _inv(
            command_id,
            project=42,
            extra_args=extra_args,
            input_file=_write(tmp_path, payload),
            yes=True,
            confirm="4",
        )
    )
    assert fake_service.call_log == [(expected_symbol, expected_kwargs)]
