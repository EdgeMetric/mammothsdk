"""Independent S2 batch-02 wire proofs.

Expected requests below are hand-authored from the public API contract.  They
are intentionally not generated from the CLI resolver or command manifest.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from mammoth.api.addons import AddonsAPI
from mammoth.api.annotations import AnnotationsAPI
from mammoth.api.browse import BrowseAPI
from mammoth.api.datasets import DatasetsAPI
from mammoth.api.files import FilesAPI
from mammoth.api.folders import FoldersAPI
from mammoth.api.notifications import NotificationsAPI
from mammoth.api.projects import ProjectsAPI
from mammoth.api.workspace import WorkspaceAPI
from mammoth.api.workspaces import WorkspacesAPI

from mammoth_cli.services import factory
from mammoth_cli.testing import login_default_profile, make_runner

CASES = [
    {"route":"addon.connector.add","argv":["addon","connector","add"],"input":{"connector_id":643},"yes":True,"api":AddonsAPI,"method":"add_connector","kwargs":{"connector_id":643},"wire":["POST","/workspaces/4/addons/connectors",{"json":{"connector_id":643}}],"response":{}},
    {"route":"addon.connector.add.connector_ids","ledger_route":"addon.connector.add","argv":["addon","connector","add"],"input":{"connector_ids":[644,645]},"yes":True,"api":AddonsAPI,"method":"add_connector","kwargs":{"connector_ids":[644,645]},"wire":["POST","/workspaces/4/addons/connectors",{"json":{"connector_ids":[644,645]}}],"response":{}},
    {"route":"annotation.create","argv":["annotation","create"],"project":41,"input":{"target_type":"dataset","target_id":751,"body":"C2_S2_BATCH02"},"api":AnnotationsAPI,"method":"create","kwargs":{"target_type":"dataset","target_id":751,"body":"C2_S2_BATCH02","project_id":41},"wire":["POST","/workspaces/4/projects/41/annotations",{"json":{"target_type":"dataset","target_id":751,"body":"C2_S2_BATCH02"}}],"response":{}},
    {"route":"browse.root","argv":["browse","root"],"input":{"fields":"C2_FIELDS","browse_type":"project","offset":5,"limit":17,"include_hidden":True},"api":BrowseAPI,"method":"root","kwargs":{"fields":"C2_FIELDS","browse_type":"project","offset":5,"limit":17,"include_hidden":True},"wire":["GET","/browse",{"params":{"fields":"C2_FIELDS","browse_type":"project","offset":5,"limit":17,"include_hidden":True}}],"response":{}},
    {"route":"browse.workspace","argv":["browse","workspace"],"input":{"level":2,"fields":"C2_WORKSPACE_FIELDS","limit":19},"api":BrowseAPI,"method":"workspace_resources","kwargs":{"level":2,"fields":"C2_WORKSPACE_FIELDS","limit":19},"wire":["GET","/workspaces/4/browse",{"params":{"level":2,"fields":"C2_WORKSPACE_FIELDS","limit":19}}],"response":{}},
    {"route":"browse.folder","argv":["browse","folder","811"],"project":41,"input":{"level":4,"fields":"C2_FOLDER_FIELDS"},"api":BrowseAPI,"method":"folder_resources","kwargs":{"folder_id":811,"project_id":41,"level":4,"fields":"C2_FOLDER_FIELDS"},"wire":["GET","/workspaces/4/projects/41/folders/811/browse",{"params":{"level":4,"fields":"C2_FOLDER_FIELDS"}}],"response":{}},
    {"route":"project.list","argv":["project","list"],"input":{"limit":23},"api":ProjectsAPI,"method":"list","kwargs":{"limit":23},"wire":["GET","/workspaces/4/projects",{"params":{"fields":"id,name","limit":23}}],"response":{"projects":[]}},
    {"route":"project.create","argv":["project","create","C2_PROJECT"],"input":{"color":"#123456","project_access":"only_me"},"api":ProjectsAPI,"method":"create","kwargs":{"name":"C2_PROJECT","color":"#123456","project_access":"only_me"},"wire":["POST","/workspaces/4/projects",{"json":{"name":"C2_PROJECT","properties":{"color":"#123456","project_access":"only_me"}}}],"response":{}},
    {"route":"project.update","argv":["project","update","47"],"project":47,"input":{"name":"C2_PROJECT_RENAMED","color":"#654321"},"api":ProjectsAPI,"method":"update","kwargs":{"project_id":47,"name":"C2_PROJECT_RENAMED","color":"#654321"},"wire":["PATCH","/workspaces/4/projects/47",{"json":{"patches":[{"op":"replace","path":"name","value":"C2_PROJECT_RENAMED"},{"op":"replace","path":"properties","value":{"color":"#654321"}}]}}],"response":{}},
    {"route":"addon.connector.remove","argv":["addon","connector","remove"],"input":{"connector_ids":[646,647]},"yes":True,"api":AddonsAPI,"method":"remove_connector","kwargs":{"connector_ids":[646,647]},"wire":["DELETE","/workspaces/4/addons/connectors",{"json":{"connector_ids":[646,647]}}],"response":{}},
    {"route":"annotation.comment.add","argv":["annotation","comment","add","753"],"project":41,"input":{"body":"C2_S2_BATCH02_COMMENT"},"api":AnnotationsAPI,"method":"comment_add","kwargs":{"annotation_id":753,"body":"C2_S2_BATCH02_COMMENT","project_id":41},"wire":["POST","/workspaces/4/projects/41/annotations/753/comments",{"json":{"body":"C2_S2_BATCH02_COMMENT"}}],"response":{}},
    {"route":"annotation.delete","argv":["annotation","delete","755"],"project":41,"yes":True,"input":None,"api":AnnotationsAPI,"method":"delete","kwargs":{"annotation_id":755,"project_id":41},"wire":["DELETE","/workspaces/4/projects/41/annotations/755",{}],"response":{}},
    {"route":"annotation.list","argv":["annotation","list"],"project":41,"input":{"target_type":"workflow","target_id":757},"api":AnnotationsAPI,"method":"list","kwargs":{"project_id":41,"target_type":"workflow","target_id":757},"wire":["GET","/workspaces/4/projects/41/annotations",{"params":{"target_type":"workflow","target_id":757}}],"response":[]},
    {"route":"annotation.update","argv":["annotation","update","759"],"project":41,"input":{"status":"resolved"},"api":AnnotationsAPI,"method":"update","kwargs":{"annotation_id":759,"status":"resolved","project_id":41},"wire":["PATCH","/workspaces/4/projects/41/annotations/759",{"json":{"status":"resolved"}}],"response":{}},
    {"route":"browse.project","argv":["browse","project"],"project":41,"input":{"fields":"C2_PROJECT_FIELDS","name":"C2_PROJECT_NAME","browse_type":"dataset","sort":"-updated_at","offset":9,"limit":27},"api":ProjectsAPI,"method":"browse","kwargs":{"project_id":41,"fields":"C2_PROJECT_FIELDS","name":"C2_PROJECT_NAME","browse_type":"dataset","sort":"-updated_at","offset":9,"limit":27},"wire":["GET","/workspaces/4/projects/41/browse",{"params":{"fields":"C2_PROJECT_FIELDS","name":"C2_PROJECT_NAME","browse_type":"dataset","sort":"-updated_at","offset":9,"limit":27}}],"response":{}},
    {"route":"dataset.list","argv":["dataset","list"],"project":41,"input":{"limit":21,"offset":0,"sort":"(name:asc)"},"api":DatasetsAPI,"method":"list","kwargs":{"project_id":41,"limit":21,"offset":0,"sort":"(name:asc)"},"wire":["GET","/workspaces/4/projects/41/datasets",{"params":{"fields":"id,name","limit":21,"offset":0,"sort":"(name:asc)"}}],"response":{"datasets":[]}},
    {"route":"dataset.get","argv":["dataset","get","763"],"project":41,"input":None,"api":DatasetsAPI,"method":"get","kwargs":{"dataset_id":763,"project_id":41},"wire":["GET","/workspaces/4/projects/41/datasets/763",{}],"response":{}},
    {"route":"dataset.rename","argv":["dataset","rename","763"],"project":41,"input":{"name":"C2_DATASET_RENAMED"},"api":DatasetsAPI,"method":"rename","kwargs":{"dataset_id":763,"name":"C2_DATASET_RENAMED","project_id":41},"wire":["PATCH","/workspaces/4/projects/41/datasets/763",{"json":{"patch":{"op":"replace","path":"name","value":"C2_DATASET_RENAMED"}}}],"response":{"name":"C2_DATASET_RENAMED"}},
    {"route":"dataset.restore","argv":["dataset","restore","763"],"project":41,"input":None,"api":DatasetsAPI,"method":"restore","kwargs":{"dataset_id":763,"project_id":41},"wire":["POST","/workspaces/4/projects/41/datasets/763/restore",{}],"response":{}},
    {"route":"file.list","argv":["file","list"],"project":41,"input":{"fields":"__full","file_ids":[801,802],"names":["C2_A","C2_B"],"statuses":["ready"],"created_at":"2026-01-01","updated_at":"2026-02-01","limit":7,"offset":3,"sort":"(id:asc)"},"api":FilesAPI,"method":"list","kwargs":{"fields":"__full","file_ids":[801,802],"names":["C2_A","C2_B"],"statuses":["ready"],"created_at":"2026-01-01","updated_at":"2026-02-01","limit":7,"offset":3,"sort":"(id:asc)"},"wire":["GET","/workspaces/4/projects/41/files",{"params":{"fields":"__full","id":"801,802","name":"C2_A,C2_B","status":"ready","created_at":"2026-01-01","updated_at":"2026-02-01","limit":7,"offset":3,"sort":"(id:asc)"}}],"response":{"files":[],"limit":7,"offset":3,"next":""}},
    {"route":"file.get","argv":["file","get","803"],"project":41,"input":{"fields":"__full"},"api":FilesAPI,"method":"get","kwargs":{"file_id":803,"fields":"__full"},"wire":["GET","/workspaces/4/projects/41/files/803",{"params":{"fields":"__full"}}],"response":{"file":{"id":803,"name":"C2_FILE"}}},
    {"route":"folder.create","argv":["folder","create","C2_FOLDER"],"project":41,"input":{"parent_resource_id":"C2_PARENT"},"api":FoldersAPI,"method":"create","kwargs":{"name":"C2_FOLDER","parent_resource_id":"C2_PARENT","project_id":41},"wire":["POST","/workspaces/4/projects/41/folders",{"json":{"name":"C2_FOLDER","parent_resource_id":"C2_PARENT"}}],"response":{"folder":{"id":901,"name":"C2_FOLDER"}}},
    {"route":"folder.get","argv":["folder","get","902"],"project":41,"input":{"fields":"__full"},"api":FoldersAPI,"method":"get","kwargs":{"folder_id":902,"project_id":41,"fields":"__full"},"wire":["GET","/workspaces/4/projects/41/folders/902",{"params":{"fields":"__full"}}],"response":{"folder":{"id":902,"name":"C2_FOLDER"}}},
    {"route":"folder.list","argv":["folder","list"],"project":41,"input":{"fields":"__full","folder_ids":[903,904],"names":["C2_A","C2_B"],"statuses":["active"],"created_at":"2026-01-01","updated_at":"2026-02-01","created_by":["C2_USER"],"limit":8,"offset":2,"sort":"(id:asc)"},"api":FoldersAPI,"method":"list","kwargs":{"fields":"__full","folder_ids":[903,904],"names":["C2_A","C2_B"],"statuses":["active"],"created_at":"2026-01-01","updated_at":"2026-02-01","created_by":["C2_USER"],"limit":8,"offset":2,"sort":"(id:asc)","project_id":41},"wire":["GET","/workspaces/4/projects/41/folders",{"params":{"fields":"__full","id":"903,904","name":"C2_A,C2_B","status":"active","created_at":"2026-01-01","updated_at":"2026-02-01","created_by":"C2_USER","limit":8,"offset":2,"sort":"(id:asc)"}}],"response":{"folders":[],"limit":8,"offset":2,"next":""}},
    {"route":"folder.update","argv":["folder","update","905"],"project":41,"input":{"name":"C2_FOLDER_RENAMED"},"api":FoldersAPI,"method":"update","kwargs":{"folder_id":905,"name":"C2_FOLDER_RENAMED","project_id":41},"wire":["PATCH","/workspaces/4/projects/41/folders/905",{"json":{"patch":[{"op":"replace","path":"name","value":"C2_FOLDER_RENAMED"}]}}],"response":{"folder":{"id":905,"name":"C2_FOLDER_RENAMED"}}},
    {"route":"addon.list","argv":["addon","list"],"input":None,"api":AddonsAPI,"method":"list","kwargs":{},"wire":["GET","/workspaces/4/addons",{}],"response":{}},
    {"route":"addon.storage.add","argv":["addon","storage","add"],"input":{"additional_storage_gb":12},"yes":True,"api":AddonsAPI,"method":"add_storage","kwargs":{"additional_storage_gb":12},"wire":["POST","/workspaces/4/addons/storage",{"json":{"additional_storage_gb":12}}],"response":{}},
    {"route":"addon.storage.remove","argv":["addon","storage","remove"],"input":{"removal_storage_gb":7},"yes":True,"api":AddonsAPI,"method":"remove_storage","kwargs":{"removal_storage_gb":7},"wire":["DELETE","/workspaces/4/addons/storage",{"json":{"removal_storage_gb":7}}],"response":{}},
    {"route":"addon.user.add","argv":["addon","user","add"],"input":{"user_count":3},"yes":True,"api":AddonsAPI,"method":"add_users","kwargs":{"user_count":3},"wire":["POST","/workspaces/4/addons/users",{"json":{"user_count":3}}],"response":{}},
    {"route":"addon.user.remove","argv":["addon","user","remove"],"input":{"user_count":2},"yes":True,"api":AddonsAPI,"method":"remove_users","kwargs":{"user_count":2},"wire":["DELETE","/workspaces/4/addons/users",{"json":{"user_count":2}}],"response":{}},
    {"route":"notification.delete","argv":["notification","delete","1001"],"input":None,"yes":True,"api":NotificationsAPI,"method":"delete","kwargs":{"notification_id":1001},"wire":["DELETE","/notifications/1001",{}],"response":{}},
    {"route":"notification.delete-batch","argv":["notification","delete-batch"],"input":{"ids":[1002,1003],"last_updated_at__lt":"2026-03-01","is_read":False},"yes":True,"api":NotificationsAPI,"method":"delete_batch","kwargs":{"ids":[1002,1003],"last_updated_at__lt":"2026-03-01","is_read":False},"wire":["DELETE","/notifications",{"params":{"ids":"1002,1003","last_updated_at__lt":"2026-03-01","is_read":False}}],"response":{}},
    {"route":"notification.list","argv":["notification","list"],"input":{"fields":"__full","last_updated_at__gte":"2026-01-01","status":"open","is_read":False,"notification_scope":"workspace","limit":9,"offset":4,"sort":"-updated_at"},"api":NotificationsAPI,"method":"list","kwargs":{"fields":"__full","last_updated_at__gte":"2026-01-01","status":"open","is_read":False,"notification_scope":"workspace","limit":9,"offset":4,"sort":"-updated_at"},"wire":["GET","/notifications",{"params":{"fields":"__full","last_updated_at__gte":"2026-01-01","status":"open","is_read":False,"notification_scope":"workspace","limit":9,"offset":4,"sort":"-updated_at"}}],"response":{}},
    {"route":"notification.update","argv":["notification","update","1004"],"input":{"patch":[{"op":"replace","path":"isRead","value":True}]},"api":NotificationsAPI,"method":"update","kwargs":{"notification_id":1004,"patch":[{"op":"replace","path":"isRead","value":True}]},"wire":["PATCH","/notifications/1004",{"json":{"patch":[{"op":"replace","path":"isRead","value":True}]}}],"response":{}},
    {"route":"notification.update-batch","argv":["notification","update-batch"],"input":{"patch":[{"op":"replace","path":"isReadMultiple","value":True}]},"api":NotificationsAPI,"method":"update_batch","kwargs":{"patch":[{"op":"replace","path":"isReadMultiple","value":True}]},"wire":["PATCH","/notifications",{"params":None,"json":{"patch":[{"op":"replace","path":"isReadMultiple","value":True}]}}],"response":{}},
    {"route":"project.checkpoint.list","argv":["project","checkpoint","list"],"project":41,"input":{"fields":"__full","sort":"-created_at","dataview_id":11,"sequence":3,"status":"ready"},"api":ProjectsAPI,"method":"checkpoint_list","kwargs":{"project_id":41,"fields":"__full","sort":"-created_at","dataview_id":11,"sequence":3,"status":"ready"},"wire":["GET","/workspaces/4/projects/41/checkpoints",{"params":{"fields":"__full","sort":"-created_at","dataview_id":11,"sequence":3,"status":"ready"}}],"response":{}},
    {"route":"project.data-check.list","argv":["project","data-check","list"],"project":41,"input":{"fields":"__full","sort":"-created_at","dataview_id":12,"sequence":4,"status":"failed"},"api":ProjectsAPI,"method":"data_check_list","kwargs":{"project_id":41,"fields":"__full","sort":"-created_at","dataview_id":12,"sequence":4,"status":"failed"},"wire":["GET","/workspaces/4/projects/41/data-checks",{"params":{"fields":"__full","sort":"-created_at","dataview_id":12,"sequence":4,"status":"failed"}}],"response":{}},
    {"route":"workspace.app-usage","argv":["workspace","app-usage"],"input":{"fields":"__full"},"api":WorkspacesAPI,"method":"app_usage","kwargs":{"fields":"__full"},"wire":["GET","/workspaces/4/app-usage",{"params":{"fields":"__full"}}],"response":{}},
    {"route":"workspace.storage-breakdown","argv":["workspace","storage-breakdown"],"input":{"limit":6,"offset":2},"api":WorkspacesAPI,"method":"storage_breakdown","kwargs":{"limit":6,"offset":2},"wire":["GET","/workspaces/4/storage-breakdown",{"params":{"limit":6,"offset":2}}],"response":{}},
    {"route":"workspace.segment.list","argv":["workspace","segment","list"],"input":None,"api":WorkspacesAPI,"method":"segment_list","kwargs":{},"wire":["GET","/workspaces/4/split-segments",{}],"response":{}},
    {"route":"workspace.list","argv":["workspace","list"],"input":{"limit":13},"api":WorkspaceAPI,"method":"list","kwargs":{"limit":13},"wire":["GET","/workspaces",{"params":{"fields":"id,name","limit":13}}],"response":{}},
    {"route":"workspace.get","argv":["workspace","get","4"],"input":None,"api":WorkspaceAPI,"method":"get","kwargs":{"workspace_id":4},"wire":["GET","/workspaces/4",{}],"response":{}},
    {"route":"workspace.delete","argv":["workspace","delete","4"],"input":None,"yes":True,"api":WorkspaceAPI,"method":"delete","kwargs":{"workspace_id":4},"wire":["DELETE","/workspaces/4",{}],"response":{}},
    {"route":"workspace.reactivate","argv":["workspace","reactivate","4"],"input":None,"yes":True,"api":WorkspaceAPI,"method":"reactivate","kwargs":{"workspace_id":4},"wire":["POST","/workspaces/4/reactivate",{}],"response":{}},
    {"route":"workspace.user.list","argv":["workspace","user","list"],"input":None,"api":WorkspaceAPI,"method":"list_users","kwargs":{"fields":"__full"},"wire":["GET","/workspaces/4/users",{"params":{"fields":"__full"}}],"response":{"users":[]}},
    {"route":"project.delete","argv":["project","delete","42"],"project":42,"input":None,"yes":True,"confirm":"42","api":ProjectsAPI,"method":"delete","kwargs":{"project_id":42},"wire":["DELETE","/workspaces/4/projects/42",{}],"response":{}},
    {"route":"project.bulk-delete","argv":["project","bulk-delete"],"input":{"project_ids":[42,43]},"yes":True,"api":ProjectsAPI,"method":"bulk_delete","kwargs":{"project_ids":[42,43]},"wire":["DELETE","/workspaces/4/projects",{"params":{"ids":"42,43"}}],"response":{}},
    {"route":"project.bulk-update","argv":["project","bulk-update"],"input":{"patch_data":{"patches":[{"op":"add","path":"role","value":[{"project_id":47,"user_roles":[{"user_id":9,"role":"project_analyst"}]}]}]}},"yes":True,"api":ProjectsAPI,"method":"bulk_update","kwargs":{"patch_data":{"patches":[{"op":"add","path":"role","value":[{"project_id":47,"user_roles":[{"user_id":9,"role":"project_analyst"}]}]}]}},"wire":["PATCH","/workspaces/4/projects",{"json":{"patches":[{"op":"add","path":"role","value":[{"project_id":47,"user_roles":[{"user_id":9,"role":"project_analyst"}]}]}]}}],"response":{}},
    {"route":"project.pending-changes","argv":["project","pending-changes"],"project":41,"input":None,"api":ProjectsAPI,"method":"pending_changes","kwargs":{"project_id":41},"wire":["GET","/workspaces/4/projects/41/pending-changes",{}],"response":{}},
    {"route":"project.publish-credentials","argv":["project","publish-credentials"],"project":41,"input":{"odbc_type":"postgres"},"api":ProjectsAPI,"method":"publish_credentials","kwargs":{"project_id":41,"odbc_type":"postgres"},"wire":["GET","/workspaces/4/projects/41/credentials",{"params":{"odbc_type":"postgres"}}],"response":{}},
    {"route":"project.resource-dependencies","argv":["project","resource-dependencies"],"project":41,"input":{"resource_ids":["r1","r2"],"is_recursive":True},"api":ProjectsAPI,"method":"resource_dependencies","kwargs":{"project_id":41,"resource_ids":["r1","r2"],"is_recursive":True},"wire":["GET","/workspaces/4/projects/41/resource-dependencies",{"params":{"resource_ids":"r1,r2","is_recursive":True}}],"response":{}},
    {"route":"project.resource-status","argv":["project","resource-status"],"project":41,"input":None,"api":ProjectsAPI,"method":"resource_status","kwargs":{"project_id":41},"wire":["GET","/workspaces/4/projects/41/resource-status",{}],"response":{}},
    {"route":"project.sample-flow","argv":["project","sample-flow"],"project":41,"input":{"label_resource_id":77},"api":ProjectsAPI,"method":"sample_flow","kwargs":{"project_id":41,"label_resource_id":77},"wire":["POST","/workspaces/4/projects/41/sample-flow",{"json":{"label_resource_id":77}}],"response":{}},
    {"route":"dataset.delete","argv":["dataset","delete","764"],"project":41,"input":None,"yes":True,"api":DatasetsAPI,"method":"delete","kwargs":{"dataset_id":764,"project_id":41},"wire":["DELETE","/workspaces/4/projects/41/datasets/764",{}],"response":{}},
    {"route":"dataset.trash","argv":["dataset","trash","765"],"project":41,"input":None,"yes":True,"api":DatasetsAPI,"method":"trash","kwargs":{"dataset_id":765,"project_id":41},"wire":["POST","/workspaces/4/projects/41/datasets/765/trash",{}],"response":{}},
]


@pytest.fixture(autouse=True)
def isolated_login(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_a, **_k: str(tmp_path),
    )
    login_default_profile()


def _argv(case: dict[str, Any]) -> list[str]:
    # project.update deliberately supplies --project 47 as the explicit
    # scope context, matching its positional target and expected URL parent.
    out = list(case["argv"])
    if case.get("project") is not None:
        out += ["--project", str(case["project"])]
    if case.get("yes"):
        out += ["--yes", "--confirm", str(case.get("confirm", "4"))]
    if case.get("input") is not None:
        out += ["--input", json.dumps(case["input"]), "--input-format", "json"]
    out += ["--output", "json", "--no-input"]
    return out


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["route"])
def test_cli_to_recording_transport_uses_independent_wire(
    case: dict[str, Any], monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    service, api = real_service(project_id=case.get("project"))
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    method, path, kwargs = case["wire"]
    api.on(method, "/api/v2" + path, body=case["response"])
    result = make_runner().invoke(_argv(case))
    assert result.exit_code == 0, result.output
    request = api.last()
    assert request.method == method
    assert request.path.removeprefix("/api/v2") == path
    assert request.json_body == kwargs.get("json")
    actual_query = {key: values[-1] for key, values in request.query.items()}
    assert actual_query == {key: str(value) for key, value in (kwargs.get("params") or {}).items()}


class RecordingClient:
    workspace_id = 4
    project_id = 41

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((method, path, kwargs))
        if "/files/" in path:
            return {"file": {}}
        if path.endswith("/files"):
            return {"files": [], "limit": 7, "offset": 3, "next": ""}
        return {}

    def _request_list(self, method: str, path: str, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append((method, path, kwargs))
        return []


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["route"])
def test_public_sdk_direct_call_matches_independent_wire(case: dict[str, Any]) -> None:
    client = RecordingClient()
    getattr(case["api"](client), case["method"])(**case["kwargs"])
    assert len(client.calls) == 1
    method, path, kwargs = client.calls[0]
    expected_method, expected_path, expected_kwargs = case["wire"]
    assert (method, path) == (expected_method, expected_path)
    assert kwargs == expected_kwargs


def test_batch02_dropped_field_control_fails_actual_wire_oracle(
    monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """A supplied field dropped by the adapter must fail the independent wire oracle."""
    case = next(c for c in CASES if c["route"] == "project.create")
    service, api = real_service(project_id=None)
    original_call = service.call

    def drop_project_access(symbol: str, **kwargs: Any) -> Any:
        if symbol.endswith("ProjectsAPI.create") or symbol.endswith("projects.create"):
            kwargs.pop("project_access", None)
        return original_call(symbol, **kwargs)

    monkeypatch.setattr(service, "call", drop_project_access)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on("POST", "/api/v2/workspaces/4/projects", body=case["response"])
    result = make_runner().invoke(_argv(case))
    # The deliberately corrupted adapter may produce a route-mismatch exit;
    # either way the recorded request is the decisive observation.
    assert result.exit_code in (0, 1, 2), result.output
    request = api.last()
    expected_json = case["wire"][2]["json"]
    assert request.json_body != expected_json
    with pytest.raises(AssertionError):
        assert request.json_body == expected_json


def test_batch02_new_annotation_adapter_drop_fails_wire_oracle(
    monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """A dropped annotation status must be caught at the transport oracle."""
    case = next(c for c in CASES if c["route"] == "annotation.update")
    service, api = real_service(project_id=41)
    original_call = service.call
    seen: list[tuple[str, dict[str, Any]]] = []

    def drop_status(symbol: str, **kwargs: Any) -> Any:
        seen.append((symbol, dict(kwargs)))
        if kwargs.get("annotation_id") == 759:
            # Keep the request valid enough to cross transport while corrupting
            # the supplied field, proving the oracle catches misrouting.
            kwargs["status"] = "open"
        return original_call(symbol, **kwargs)

    monkeypatch.setattr(service, "call", drop_status)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on("PATCH", "/api/v2/workspaces/4/projects/41/annotations/759", body=case["response"])
    result = make_runner().invoke(_argv(case))
    assert seen, result.output
    assert result.exit_code in (0, 1, 2), result.output
    request = api.last()
    assert request.json_body != case["wire"][2]["json"]
    with pytest.raises(AssertionError):
        assert request.json_body == case["wire"][2]["json"]


def test_batch02_folder_update_adapter_mutation_fails_wire_oracle(
    monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """A renamed folder field changed by the adapter must fail the wire oracle."""
    case = next(c for c in CASES if c["route"] == "folder.update")
    service, api = real_service(project_id=41)
    original_call = service.call

    def misroute_name(symbol: str, **kwargs: Any) -> Any:
        if kwargs.get("folder_id") == 905:
            kwargs["name"] = "C2_WRONG_NAME"
        return original_call(symbol, **kwargs)

    monkeypatch.setattr(service, "call", misroute_name)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on("PATCH", "/api/v2/workspaces/4/projects/41/folders/905", body=case["response"])
    result = make_runner().invoke(_argv(case))
    assert result.exit_code in (0, 1, 2), result.output
    request = api.last()
    assert request.json_body != case["wire"][2]["json"]
    with pytest.raises(AssertionError):
        assert request.json_body == case["wire"][2]["json"]


def test_batch02_addon_storage_adapter_mutation_fails_wire_oracle(
    monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """A changed addon quantity must be visible to the independent wire oracle."""
    case = next(c for c in CASES if c["route"] == "addon.storage.add")
    service, api = real_service(project_id=None)
    original_call = service.call

    def misroute_storage(symbol: str, **kwargs: Any) -> Any:
        if "additional_storage_gb" in kwargs:
            kwargs["additional_storage_gb"] = 99
        return original_call(symbol, **kwargs)

    monkeypatch.setattr(service, "call", misroute_storage)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on("POST", "/api/v2/workspaces/4/addons/storage", body=case["response"])
    result = make_runner().invoke(_argv(case))
    assert result.exit_code in (0, 1, 2), result.output
    request = api.last()
    assert request.json_body != case["wire"][2]["json"]
    with pytest.raises(AssertionError):
        assert request.json_body == case["wire"][2]["json"]


def test_batch02_workspace_storage_adapter_mutation_fails_wire_oracle(
    monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """A changed storage offset must be visible to the independent wire oracle."""
    case = next(c for c in CASES if c["route"] == "workspace.storage-breakdown")
    service, api = real_service(project_id=None)
    original_call = service.call

    def misroute_offset(symbol: str, **kwargs: Any) -> Any:
        if "offset" in kwargs:
            kwargs["offset"] = 99
        return original_call(symbol, **kwargs)

    monkeypatch.setattr(service, "call", misroute_offset)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on("GET", "/api/v2/workspaces/4/storage-breakdown", body=case["response"])
    result = make_runner().invoke(_argv(case))
    assert result.exit_code in (0, 1, 2), result.output
    request = api.last()
    actual_query = {key: values[-1] for key, values in request.query.items()}
    assert actual_query != {key: str(value) for key, value in case["wire"][2]["params"].items()}
    with pytest.raises(AssertionError):
        assert actual_query == {
            key: str(value) for key, value in case["wire"][2]["params"].items()
        }


def test_batch02_project_bulk_update_adapter_mutation_fails_wire_oracle(
    monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """A changed bulk project patch must fail the independent wire oracle."""
    case = next(c for c in CASES if c["route"] == "project.bulk-update")
    service, api = real_service(project_id=None)
    original_call = service.call

    def misroute_patch(symbol: str, **kwargs: Any) -> Any:
        if "patch_data" in kwargs:
            kwargs["patch_data"] = {"patches": [{"op": "remove", "path": "role", "value": []}]}
        return original_call(symbol, **kwargs)

    monkeypatch.setattr(service, "call", misroute_patch)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on("PATCH", "/api/v2/workspaces/4/projects", body=case["response"])
    result = make_runner().invoke(_argv(case))
    assert result.exit_code in (0, 1, 2), result.output
    request = api.last()
    assert request.json_body != case["wire"][2]["json"]
    with pytest.raises(AssertionError):
        assert request.json_body == case["wire"][2]["json"]


def test_dataset_list_nonzero_offset_cli_wire_in_venv314(
    monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """CLI regression: explicit nonzero offset reaches the SDK transport."""
    service, api = real_service(project_id=41)
    seen: list[dict[str, Any]] = []
    original_call = service.call

    def record_call(symbol: str, **kwargs: Any) -> Any:
        if "DatasetsAPI.list" in symbol:
            seen.append(dict(kwargs))
        return original_call(symbol, **kwargs)

    monkeypatch.setattr(service, "call", record_call)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on("GET", "/api/v2/workspaces/4/projects/41/datasets", body={"datasets": []})
    argv = [
        "dataset", "list", "--project", "41",
        "--input", json.dumps({"limit": 1, "offset": 6, "sort": "(name:asc)"}),
        "--input-format", "json", "--output", "json",
    ]
    result = make_runner().invoke(argv)
    assert result.exit_code == 0, result.output
    assert seen and seen[0].get("offset") == 6, seen
    request = api.last()
    assert {key: values[-1] for key, values in request.query.items()} == {
        "fields": "id,name", "limit": "1", "offset": "6", "sort": "(name:asc)"
    }


def test_dataset_list_nonzero_offset_cli_wire_in_mandatory_no_input_mode(
    monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """The same offset contract must hold in agent/``--no-input`` mode."""
    service, api = real_service(project_id=41)
    seen: list[dict[str, Any]] = []
    original_call = service.call

    def record_call(symbol: str, **kwargs: Any) -> Any:
        if "DatasetsAPI.list" in symbol:
            seen.append(dict(kwargs))
        return original_call(symbol, **kwargs)

    monkeypatch.setattr(service, "call", record_call)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on("GET", "/api/v2/workspaces/4/projects/41/datasets", body={"datasets": []})
    argv = [
        "dataset", "list", "--project", "41",
        "--input", json.dumps({"limit": 1, "offset": 6, "sort": "(name:asc)"}),
        "--input-format", "json", "--output", "json", "--no-input",
    ]
    result = make_runner().invoke(argv)
    assert result.exit_code == 0, result.output
    assert seen and seen[0].get("offset") == 6, seen
    request = api.last()
    assert {key: values[-1] for key, values in request.query.items()} == {
        "fields": "id,name", "limit": "1", "offset": "6", "sort": "(name:asc)"
    }
