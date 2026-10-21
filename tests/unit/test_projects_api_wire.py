"""ProjectsAPI: wire requests, paging, name resolution, attention digest and validation.

Routes, query names and body shapes come from the pinned prod OpenAPI spec
(GetProject, CreateProject, CopyProject, UpdateProject, DeleteProjects, AddUserProject,
RemoveUserProject, UpdateUserProject, BrowseProjectProjects, GetProjectCheckpoints,
GetProjectDataChecks, GetPendingChanges, GetPublishCredentials, GetResourceDependencies,
CreateSampleFlow, BulkGetResources). The agent-memory PATCH ops (``add``/``remove`` on
``agent_memory``) are in the spec's ``PatchPathValues`` and are described in
mvc-service ``apiv2/apiv2/projects/controller.py`` (commit 8b634c538d).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothDeletionVerificationError, MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema, spec

WS = "/workspaces/1/projects"


def _req(server: RecordingServer, i: int = -1) -> dict[str, Any]:
    return server.requests[i]


def _query_names(path: str, method: str) -> set[str]:
    op = spec()["paths"][path][method]
    return {p["name"] for p in op.get("parameters", []) if p["in"] == "query"}


# --- listing ------------------------------------------------------------------------------------


async def test_list_defaults_ask_for_member_projects_only(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {WS}"] = {"projects": [{"id": 1, "name": "A"}]}
    page = await client.projects.list()
    assert server.requests == [
        {
            "method": "GET",
            "path": WS,
            "query": {"fields": "id,name", "limit": "100", "subscribed": "true"},
            "body": None,
        }
    ]
    assert page == {"projects": [{"id": 1, "name": "A"}]}
    assert set(_req(server)["query"]) <= _query_names("/workspaces/{workspace_id}/projects", "get")


async def test_list_with_offset_and_explicit_workspace(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /workspaces/9/projects"] = {"projects": []}
    await client.projects.list(workspace_id=9, limit=5, offset=20, fields="id")
    assert _req(server)["path"] == "/workspaces/9/projects"
    assert _req(server)["query"] == {
        "fields": "id",
        "limit": "5",
        "offset": "20",
        "subscribed": "true",
    }


async def test_list_including_non_members_tags_each_project_with_membership(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    # The same route answers differently by the `subscribed` filter: the unfiltered list holds
    # both projects, the subscribed (member) list only project 2.
    class BySubscribed(dict[str, Any]):
        def get(self, key: str, default: Any = None) -> Any:
            if server.requests[-1]["query"].get("subscribed") == "true":
                return (200, {"projects": [{"id": 2}]})
            return (200, {"projects": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]})

    server.answers = BySubscribed()
    page = await client.projects.list(include_non_members=True)
    first = _req(server, 0)
    assert "subscribed" not in first["query"]
    second = _req(server, 1)
    assert second["query"] == {"fields": "id", "limit": "100", "subscribed": "true"}
    assert [(p["id"], p["member"]) for p in page["projects"]] == [(1, False), (2, True)]


async def test_list_all_follows_offsets_until_a_short_page(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    pages = {
        None: [{"id": i, "name": f"P{i}"} for i in range(100)],
        "100": [{"id": i, "name": f"P{i}"} for i in range(100, 130)],
    }

    class Switching(dict[str, Any]):  # answer by the offset the SDK asked for
        def get(self, key: str, default: Any = None) -> Any:
            return (200, {"projects": pages[server.requests[-1]["query"].get("offset")]})

    server.answers = Switching()
    rows = await client.projects.list_all()
    assert [r["id"] for r in rows] == list(range(130))
    offsets = [r["query"].get("offset") for r in server.requests]
    assert offsets == [None, "100"]
    assert all(r["query"]["limit"] == "100" for r in server.requests)


async def test_list_all_stops_when_the_server_ignores_offset(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    same_page = [{"id": i, "name": f"P{i}"} for i in range(100)]
    server.answers[f"GET {WS}"] = {"projects": same_page}
    rows = await client.projects.list_all()
    assert len(rows) == 100
    assert len(server.requests) == 2  # the repeat page adds nothing, so paging stops


async def test_list_all_including_non_members_tags_membership(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {WS}"] = {"projects": [{"id": 3, "name": "C"}]}
    rows = await client.projects.list_all(include_non_members=True)
    assert rows == [{"id": 3, "name": "C", "member": True}]
    assert "subscribed" not in _req(server, 0)["query"]


# --- get / name resolution ------------------------------------------------------------------


async def _answer_projects(server: RecordingServer, rows: list[dict[str, Any]]) -> None:
    server.answers[f"GET {WS}"] = {"projects": rows}


async def test_get_by_id_returns_id_and_name_and_does_not_limit_to_members(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await _answer_projects(server, [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
    assert await client.projects.get(2) == {"id": 2, "name": "B"}
    assert "subscribed" not in _req(server)["query"]


async def test_get_unknown_id_lists_the_available_projects(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await _answer_projects(server, [{"id": 1, "name": "A"}])
    with pytest.raises(ValueError, match=r"Project ID 5 not found.*\[\('A', 1\)\]"):
        await client.projects.get(5)


async def test_get_without_argument_picks_the_only_member_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await _answer_projects(server, [{"id": 1, "name": "Only"}])
    assert await client.projects.get() == {"id": 1, "name": "Only"}
    assert _req(server)["query"]["subscribed"] == "true"


async def test_get_without_argument_among_several_asks_to_choose(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await _answer_projects(server, [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
    with pytest.raises(
        ValueError, match=r"(?s)Multiple projects found \(2\).*A \(ID: 1\).*B \(ID: 2\)"
    ):
        await client.projects.get()


async def test_get_by_name(server: RecordingServer, client: MammothClient) -> None:  # noqa: F811
    await _answer_projects(server, [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
    assert await client.projects.get("B") == {"id": 2, "name": "B"}


async def test_get_by_unknown_name(
    server: RecordingServer, client: MammothClient
) -> None:  # noqa: F811
    await _answer_projects(server, [{"id": 1, "name": "A"}])
    with pytest.raises(ValueError, match=r"Project 'Z' not found.*\['A'\]"):
        await client.projects.get("Z")


async def test_get_by_duplicate_name_asks_for_the_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await _answer_projects(server, [{"id": 1, "name": "A"}, {"id": 2, "name": "A"}])
    with pytest.raises(ValueError, match=r"(?s)Multiple projects found with name 'A'.*by ID"):
        await client.projects.get("A")


async def test_get_with_no_projects_in_the_workspace(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await _answer_projects(server, [])
    with pytest.raises(ValueError, match="No projects found in workspace"):
        await client.projects.get()


async def test_get_rejects_other_types(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await _answer_projects(server, [{"id": 1, "name": "A"}])
    with pytest.raises(ValueError, match="Invalid project type: <class 'float'>"):
        await client.projects.get(1.5)  # type: ignore[arg-type]


# --- create / copy / update / delete ----------------------------------------------------------


async def test_create_sends_name_and_properties(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.create("Sales", color="#E3E5E8", project_access="only_me")
    assert _req(server) == {
        "method": "POST",
        "path": WS,
        "query": {},
        "body": {"name": "Sales", "properties": {"color": "#E3E5E8", "project_access": "only_me"}},
    }
    assert "only_me" in schema("ProjectAccessValues")["enum"]


async def test_create_always_sends_the_required_properties_object(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.create("Sales")
    assert _req(server)["body"] == {"name": "Sales", "properties": {}}
    assert "properties" in schema("ProjectCreate")["required"]


async def test_copy_sends_the_spec_body_with_defaults(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.copy(7, "Sales (copy)")
    assert _req(server) == {
        "method": "POST",
        "path": f"{WS}/7/copy",
        "query": {},
        "body": {
            "name": "Sales (copy)",
            "dataset_ids": None,
            "include_dashboards": False,
            "exclude_data": False,
        },
    }
    props = schema("CopyProjectRequest")["properties"]
    assert set(_req(server)["body"]) == set(props)


async def test_copy_sends_dataset_selection_and_flags(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.copy(
        7, "X", dataset_ids=[11, 12], include_dashboards=True, exclude_data=True, workspace_id=4
    )
    assert _req(server)["path"] == "/workspaces/4/projects/7/copy"
    assert _req(server)["body"] == {
        "name": "X",
        "dataset_ids": [11, 12],
        "include_dashboards": True,
        "exclude_data": True,
    }


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"project_id": 0, "name": "n"}, "positive integer, got 0"),
        ({"project_id": True, "name": "n"}, "positive integer, got True"),
        ({"project_id": 1, "name": ""}, "1 to 63 characters"),
        ({"project_id": 1, "name": "x" * 64}, "1 to 63 characters"),
        ({"project_id": 1, "name": "n", "dataset_ids": []}, "at least one dataset id"),
    ],
)
async def test_copy_rejects_invalid_arguments_before_any_request(
    kwargs: dict[str, Any],
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.projects.copy(**kwargs)
    assert server.requests == []


async def test_copy_name_limit_matches_the_spec() -> None:
    assert schema("CopyProjectRequest")["properties"]["name"]["maxLength"] == 63


async def test_update_name_and_color_are_separate_patches(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.update(7, name="New", color="#fff")
    assert _req(server) == {
        "method": "PATCH",
        "path": f"{WS}/7",
        "query": {},
        "body": {
            "patches": [
                {"op": "replace", "path": "name", "value": "New"},
                {"op": "replace", "path": "properties", "value": {"color": "#fff"}},
            ]
        },
    }
    assert {"name", "properties"} <= set(schema("PatchPathValues")["enum"])


async def test_update_requires_something_to_change(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="at least one of `name` or `color`"):
        await client.projects.update(7)
    assert server.requests == []


async def test_delete_and_bulk_delete_and_bulk_update(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.delete(7)
    await client.projects.bulk_delete([7, 8])
    await client.projects.bulk_update({"patches": []})
    assert server.requests == [
        {"method": "DELETE", "path": f"{WS}/7", "query": {}, "body": None},
        {"method": "DELETE", "path": WS, "query": {"ids": "7,8"}, "body": None},
        {"method": "PATCH", "path": WS, "query": {}, "body": {"patches": []}},
    ]


async def test_delete_and_verify_returns_once_the_project_is_gone(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {WS}/7"] = (200, {"deleted": True})
    server.answers[f"GET {WS}"] = {"projects": [{"id": 2}]}
    result = await client.projects.delete_and_verify(7, poll_interval=0.01)
    assert result == {
        "project_id": 7,
        "status": "deleted",
        "verified": True,
        "ack": {"deleted": True},
    }
    check = _req(server)
    assert check["path"] == WS and "subscribed" not in check["query"]
    assert check["query"]["fields"] == "id"


async def test_delete_and_verify_times_out_while_the_project_is_still_listed(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {WS}/7"] = (200, {"deleted": True})
    server.answers[f"GET {WS}"] = {"projects": [{"id": 7}, {"id": 2}]}
    with pytest.raises(MammothDeletionVerificationError) as exc:
        await client.projects.delete_and_verify(7, timeout=0, poll_interval=0.01)
    assert "absence was not verified" in str(exc.value)
    details = exc.value.details
    assert details["still_present"] == [7]
    assert details["project_ids"] == [7] and details["verified"] is False
    assert details["ack"] == {"deleted": True}


async def test_bulk_delete_and_verify_reports_every_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {WS}"] = (200, {"ok": True})
    server.answers[f"GET {WS}"] = {"projects": []}
    result = await client.projects.bulk_delete_and_verify([7, 8], poll_interval=0.01)
    assert result == {
        "project_ids": [7, 8],
        "status": "deleted",
        "verified": True,
        "ack": {"ok": True},
    }
    assert server.requests[0]["query"] == {"ids": "7,8"}


async def test_bulk_delete_and_verify_names_the_ids_still_present(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {WS}"] = (200, {"ok": True})
    server.answers[f"GET {WS}"] = {"projects": [{"id": 8}]}
    with pytest.raises(MammothDeletionVerificationError) as exc:
        await client.projects.bulk_delete_and_verify([7, 8], timeout=0, poll_interval=0.01)
    assert exc.value.details["still_present"] == [8]


# --- users ----------------------------------------------------------------------------------


async def test_add_users_accepts_numeric_strings_and_sets_role(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.add_users(7, [3, "4"], role="project_admin")
    assert _req(server) == {
        "method": "POST",
        "path": f"{WS}/7/users",
        "query": {},
        "body": {
            "users": [
                {"user_id": 3, "role": "project_admin"},
                {"user_id": 4, "role": "project_admin"},
            ]
        },
    }


async def test_add_users_without_role_leaves_the_server_default(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.add_users(7, [3])
    assert _req(server)["body"] == {"users": [{"user_id": 3}]}
    assert schema("AddUserSpec")["properties"]["role"]["default"] == "project_analyst"


@pytest.mark.parametrize("bad", ["a@b.c", True, 1.5, None])
async def test_add_users_rejects_non_numeric_ids(
    bad: Any, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="user_ids must be numeric user ids"):
        await client.projects.add_users(7, [3, bad])
    assert server.requests == []


async def test_add_users_requires_at_least_one(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="at least one user id"):
        await client.projects.add_users(7, [])
    assert server.requests == []


async def test_remove_users_sends_one_request_per_user(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {WS}/7/users"] = {"removed": True}
    result = await client.projects.remove_users(7, ["3", "4"])
    assert [(r["method"], r["path"], r["query"]) for r in server.requests] == [
        ("DELETE", f"{WS}/7/users", {"user_id": "3"}),
        ("DELETE", f"{WS}/7/users", {"user_id": "4"}),
    ]
    assert result == {"removed": True}
    assert _query_names("/workspaces/{workspace_id}/projects/{project_id}/users", "delete") == {
        "user_id"
    }


async def test_remove_users_requires_at_least_one(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="at least one user id"):
        await client.projects.remove_users(7, [])
    assert server.requests == []


async def test_user_update_by_user_id_patches_permissions(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.user_update(7, "project_admin", user_id=3)
    assert _req(server) == {
        "method": "PATCH",
        "path": f"{WS}/7/users",
        "query": {"user_id": "3"},
        "body": {"patch": [{"op": "replace", "path": "permissions", "value": "project_admin"}]},
    }
    assert schema("ProjectUserPatch")["examples"][0] == _req(server)["body"] | {
        "patch": [{"op": "replace", "path": "permissions", "value": "project_admin"}]
    }


async def test_user_update_by_invite_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.user_update(7, "project_analyst", invite_id=9)
    assert _req(server)["query"] == {"invite_id": "9"}


@pytest.mark.parametrize("ids", [{}, {"user_id": 1, "invite_id": 2}])
async def test_user_update_needs_exactly_one_of_user_or_invite(
    ids: dict[str, int], server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="Exactly one of `user_id` or `invite_id`"):
        await client.projects.user_update(7, "project_admin", **ids)
    assert server.requests == []


# --- browse and read-only listings -----------------------------------------------------------


async def test_browse_sends_only_the_given_params(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.browse(
        7, fields="id", name="q", browse_type="datasets", sort="(id:asc)", offset=5, limit=10
    )
    assert _req(server) == {
        "method": "GET",
        "path": f"{WS}/7/browse",
        "query": {
            "fields": "id",
            "name": "q",
            "browse_type": "datasets",
            "sort": "(id:asc)",
            "offset": "5",
            "limit": "10",
        },
        "body": None,
    }
    assert set(_req(server)["query"]) <= _query_names(
        "/workspaces/{workspace_id}/projects/{project_id}/browse", "get"
    )


async def test_browse_without_params_sends_no_query(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.browse(7)
    assert _req(server)["query"] == {}


@pytest.mark.parametrize(
    ("method", "route"), [("checkpoint_list", "checkpoints"), ("data_check_list", "data-checks")]
)
async def test_project_checkpoint_and_data_check_lists(
    method: str, route: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    call = getattr(client.projects, method)
    await call(7, fields="id", sort="(id:asc)", dataview_id=3, sequence=2, status="failed")
    assert _req(server) == {
        "method": "GET",
        "path": f"{WS}/7/{route}",
        "query": {
            "fields": "id",
            "sort": "(id:asc)",
            "dataview_id": "3",
            "sequence": "2",
            "status": "failed",
        },
        "body": None,
    }
    declared = _query_names(f"/workspaces/{{workspace_id}}/projects/{{project_id}}/{route}", "get")
    assert set(_req(server)["query"]) == declared
    await call(7)
    assert _req(server)["query"] == {}


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.checkpoint_list(0),
        lambda p: p.data_check_list(-1),
        lambda p: p.pending_changes(0),
        lambda p: p.needs_attention(0),
        lambda p: p.list_agent_memory(0),
        lambda p: p.add_agent_memory(0, "x"),
        lambda p: p.remove_agent_memory(0, 1),
        lambda p: p.publish_credentials(0, "postgres"),
        lambda p: p.resource_dependencies(0, ["a"]),
        lambda p: p.resource_dependencies_update(0, []),
        lambda p: p.resource_status(0),
        lambda p: p.sample_flow(0),
        lambda p: p.user_update(0, "project_admin", user_id=1),
    ],
)
async def test_non_positive_project_ids_are_refused_before_any_request(
    call: Callable[[Any], Awaitable[Any]],
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`project_id` must be a positive integer"):
        await call(client.projects)
    assert server.requests == []


async def test_credentials_resources_and_sample_flow_wire(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.projects.publish_credentials(7, "bigquery")
    await client.projects.resource_dependencies(7, ["dataview_1", "dataset_2"], is_recursive=True)
    await client.projects.resource_dependencies(7, ["dataview_1"])
    await client.projects.resource_status(7)
    await client.projects.pending_changes(7, workspace_id=4)
    await client.projects.sample_flow(7)
    await client.projects.sample_flow(7, label_resource_id=33)
    got = [(r["method"], r["path"], r["query"], r["body"]) for r in server.requests]
    assert got == [
        ("GET", f"{WS}/7/credentials", {"odbc_type": "bigquery"}, None),
        (
            "GET",
            f"{WS}/7/resource-dependencies",
            {"resource_ids": "dataview_1,dataset_2", "is_recursive": "true"},
            None,
        ),
        ("GET", f"{WS}/7/resource-dependencies", {"resource_ids": "dataview_1"}, None),
        ("GET", f"{WS}/7/resource-status", {}, None),
        ("GET", "/workspaces/4/projects/7/pending-changes", {}, None),
        ("POST", f"{WS}/7/sample-flow", {}, {}),
        ("POST", f"{WS}/7/sample-flow", {}, {"label_resource_id": 33}),
    ]


async def test_resource_dependencies_update_rejects_bad_workspace_and_duplicates(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    patch = {
        "op": "replace",
        "path": "data_sync",
        "value": {"context_type": "dataview", "context_id": 5, "data_pass_through": True},
    }
    with pytest.raises(MammothValidationError, match="`workspace_id` must be a positive"):
        await client.projects.resource_dependencies_update(7, [patch], workspace_id=0)  # type: ignore[list-item]
    with pytest.raises(MammothValidationError, match="at least one operation"):
        await client.projects.resource_dependencies_update(7, [])
    with pytest.raises(MammothValidationError, match="must not repeat a resource target"):
        await client.projects.resource_dependencies_update(7, [patch, patch])  # type: ignore[list-item]
    with pytest.raises(MammothValidationError, match="Invalid data-sync patch"):
        await client.projects.resource_dependencies_update(7, [{"op": "add"}])  # type: ignore[list-item]
    assert server.requests == []


# --- agent memory -----------------------------------------------------------------------------


async def test_add_agent_memory_patches_the_caller_list_and_returns_items(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"PATCH {WS}/7"] = {"id": 7, "properties": {"agent_memory": ["a", "b"]}}
    result = await client.projects.add_agent_memory(7, "b")
    assert _req(server) == {
        "method": "PATCH",
        "path": f"{WS}/7",
        "query": {},
        "body": {"patches": [{"op": "add", "path": "agent_memory", "value": "b"}]},
    }
    assert result == {"items": ["a", "b"]}
    assert "agent_memory" in schema("PatchPathValues")["enum"]


async def test_remove_agent_memory_sends_the_index(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"PATCH {WS}/7"] = {"id": 7, "properties": {}}
    result = await client.projects.remove_agent_memory(7, 1)
    assert _req(server)["body"] == {
        "patches": [{"op": "remove", "path": "agent_memory", "value": 1}]
    }
    assert result == {"items": []}


async def test_list_agent_memory_reads_the_callers_items_from_the_project_list(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {WS}"] = {
        "projects": [
            {"id": 6, "properties": {"agent_memory": ["other"]}},
            {"id": 7, "properties": {"agent_memory": ["dates as DD-MM-YYYY"]}},
        ]
    }
    assert await client.projects.list_agent_memory(7) == {"items": ["dates as DD-MM-YYYY"]}
    assert _req(server)["query"]["fields"] == "id,properties"


async def test_list_agent_memory_of_a_project_without_memory_is_empty(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {WS}"] = {"projects": [{"id": 7, "properties": None}]}
    assert await client.projects.list_agent_memory(7) == {"items": []}


async def test_list_agent_memory_of_an_unknown_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {WS}"] = {"projects": [{"id": 6}]}
    with pytest.raises(ValueError, match="Project ID 7 not found"):
        await client.projects.list_agent_memory(7)


# --- needs_attention --------------------------------------------------------------------------


def _attention_server(server: RecordingServer) -> None:
    server.answers[f"GET {WS}/7/pending-changes"] = {
        "pending_items": {
            "pending_changes": {
                "11": {
                    "dataview_id": 11,
                    "dataview_name": "Orders view",
                    "datasource_name": "Orders",
                    "is_pipeline_in_error": True,
                    "pending_steps_count": 2,
                    "tasks_in_error": {"t1": {"msg": "bad"}},
                    "actions_in_error": {},
                },
                "12": {
                    "dataview_id": 12,
                    "dataview_name": "Stock view",
                    "datasource_name": "Stock",
                    "is_pipeline_in_error": False,
                    "pending_steps_count": 1,
                    "tasks_in_error": {},
                    "actions_in_error": {},
                },
                "summary": {"note": "not a view"},
            },
            "ds_action_needed_items": [
                {
                    "id": 40,
                    "name": "upload.csv",
                    "resource_type": "datasource",
                    "action_needed": {"type": "confirm_schema"},
                    "append_to_ds_id": None,
                },
                {
                    "id": 41,
                    "name": "a file",
                    "resource_type": "file",
                    "action_needed": {"type": "password"},
                    "needs_review": False,
                },
            ],
            "pending_data_update_items": [
                {
                    "op_id": 1,
                    "op_type": "join",
                    "op_name": "Join A",
                    "source_dataview_id": 11,
                    "data_update_pending": True,
                    "data_pass_through": False,
                    "resource": {},
                },
                {
                    "op_id": 2,
                    "op_type": "join",
                    "op_name": "Join B",
                    "source_dataview_id": 99,
                    "data_update_pending": False,
                    "data_pass_through": False,
                    "resource": {},
                },
            ],
        }
    }
    server.answers[f"GET {WS}/7/checkpoints"] = {
        "checkpoints": [
            {
                "id": 1,
                "dataview_id": 12,
                "name": "approve",
                "status": "needs_approval",
                "checkpoint_type": "approval",
            },
            {"id": 2, "dataview_id": 12, "status": "approved", "checkpoint_type": "approval"},
            {"id": 3, "dataview_id": 12, "status": "needs_approval", "checkpoint_type": "alert"},
        ]
    }
    server.answers[f"GET {WS}/7/data-checks"] = {
        "data_checks": [
            {"id": 5, "dataview_id": 77, "status": "failed"},
            {"id": 6, "dataview_id": 12, "status": "passed"},
        ]
    }
    server.answers[f"POST {WS}/7/resources/bulk"] = (
        201,
        {
            "resources": [
                {
                    "id": 1,
                    "resource_type": "dataview",
                    "object_id": 11,
                    "name": "Orders view",
                    "dataset": {"id": 100, "name": "Orders"},
                },
                {
                    "id": 2,
                    "resource_type": "dataview",
                    "object_id": 12,
                    "name": "Stock view",
                    "dataset": {"id": 200, "name": "Stock"},
                },
                {"id": 3, "resource_type": "dataview", "object_id": 13, "dataset": None},
            ]
        },
    )


async def test_needs_attention_digests_pending_checkpoints_and_data_checks(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _attention_server(server)
    result = await client.projects.needs_attention(7)

    by_kind = {k: [i for i in result["items"] if i["kind"] == k] for k in result["counts"]}
    assert result["counts"] == {
        "pipeline_error": 1,
        "pending_pipeline": 1,
        "needs_input": 2,
        "pending_data": 1,
        "checkpoint": 1,
        "data_check": 1,
    }
    err = by_kind["pipeline_error"][0]
    assert (err["view_id"], err["view_name"], err["dataset_id"], err["dataset_name"]) == (
        11,
        "Orders view",
        100,
        "Orders",
    )
    assert err["tasks_in_error"] == [{"msg": "bad"}] and err["pending_steps_count"] == 2
    pending = by_kind["pending_pipeline"][0]
    assert (pending["view_id"], pending["dataset_id"]) == (12, 200)
    needs = {i["name"]: i for i in by_kind["needs_input"]}
    assert needs["upload.csv"]["dataset_id"] == 40  # a datasource row names its dataset
    assert needs["upload.csv"]["action"] == "confirm_schema"
    assert needs["a file"]["dataset_id"] is None and needs["a file"]["needs_review"] is False
    assert by_kind["pending_data"][0]["view_id"] == 11
    assert by_kind["pending_data"][0]["operation_name"] == "Join A"
    assert by_kind["checkpoint"][0]["checkpoint_id"] == 1  # only the approval awaiting approval
    assert by_kind["data_check"][0]["data_check_id"] == 5
    # View 77 (data check) is not known to the project; it is reported, not dropped.
    assert result["unresolved_view_ids"] == [77]
    assert {d["dataset_id"] for d in result["datasets"]} == {100, 200, 40}
    ds_100 = next(d for d in result["datasets"] if d["dataset_id"] == 100)
    assert ds_100["view_ids"] == [11]
    ds_40 = next(d for d in result["datasets"] if d["dataset_id"] == 40)
    assert ds_40 == {"dataset_id": 40, "dataset_name": "upload.csv", "view_ids": []}
    assert result["project_id"] == 7

    bulk = [r for r in server.requests if r["path"].endswith("/resources/bulk")]
    assert len(bulk) == 1
    assert bulk[0]["body"] == {"ids": [{"type": "dataview", "id": v} for v in (11, 12, 77)]}


async def test_needs_attention_on_a_quiet_project_is_empty(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {WS}/7/pending-changes"] = {"pending_items": {}}
    server.answers[f"GET {WS}/7/checkpoints"] = {"checkpoints": []}
    server.answers[f"GET {WS}/7/data-checks"] = {"data_checks": []}
    result = await client.projects.needs_attention(7)
    assert result == {
        "project_id": 7,
        "items": [],
        "datasets": [],
        "counts": {},
        "unresolved_view_ids": [],
    }


async def test_delete_and_verify_polls_until_the_project_disappears(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    lists = [{"projects": [{"id": 7}]}, {"projects": [{"id": 7}]}, {"projects": []}]

    class Scripted(dict[str, Any]):
        def get(self, key: str, default: Any = None) -> Any:
            if key.startswith("DELETE"):
                return (200, {"deleted": True})
            polled = sum(1 for r in server.requests if r["method"] == "GET")
            return (200, lists[polled - 1])

    server.answers = Scripted()
    result = await client.projects.delete_and_verify(7, timeout=30, poll_interval=0.01)
    assert result["verified"] is True
    assert [r["method"] for r in server.requests] == ["DELETE", "GET", "GET", "GET"]


async def test_resource_dependencies_update_sends_only_the_fields_that_were_set(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    patches = [
        {
            "op": "replace",
            "path": "data_sync",
            "value": {"context_type": "task", "context_id": 5, "run_pending_update": True},
        }
    ]
    await client.projects.resource_dependencies_update(7, patches, workspace_id=4)  # type: ignore[arg-type]
    assert _req(server) == {
        "method": "PATCH",
        "path": "/workspaces/4/projects/7/resource-dependencies",
        "query": {},
        "body": {"patches": patches},
    }
