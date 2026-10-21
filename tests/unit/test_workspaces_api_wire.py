"""WorkspacesAPI wire requests held to the pinned spec (users, invites, segments, home, usage).

Spec operations: GetUsersInWorkspace, AddUserInWorkspace (UserInvitePost), RemoveUserFromWorkspace,
UpdateUserToWorkspace (WorkspaceUsersPatch), GetSegments, UpdateSegments, GetStorageBreakdown,
GetHomeSummary, GetAppUsage.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema, spec

W = "/workspaces/1"


def _declared(path: str, method: str) -> set[str]:
    op = spec()["paths"][path][method]
    return {p["name"] for p in op.get("parameters", []) if p["in"] == "query"}


def _only(server: RecordingServer) -> dict[str, Any]:
    assert len(server.requests) == 1
    return server.requests[0]


# --- plain GET routes -------------------------------------------------------------------------


async def test_home_summary_and_segment_list_hit_their_spec_routes(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.home_summary()
    await client.workspace.segment_list()
    assert [(r["method"], r["path"], r["query"]) for r in server.requests] == [
        ("GET", f"{W}/home", {}),
        ("GET", f"{W}/split-segments", {}),
    ]


async def test_storage_breakdown_sends_only_the_paging_it_was_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.storage_breakdown()
    await client.workspace.storage_breakdown(limit=5, offset=0)
    assert [r["query"] for r in server.requests] == [{}, {"limit": "5", "offset": "0"}]
    assert {"limit", "offset"} <= _declared("/workspaces/{workspace_id}/storage-breakdown", "get")
    assert all(r["path"] == f"{W}/storage-breakdown" for r in server.requests)


# --- segments ---------------------------------------------------------------------------------


async def test_segment_update_wraps_the_operations_in_patch(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    ops = [{"op": "replace", "path": "x", "value": 1}]
    await client.workspace.segment_update(ops)
    assert _only(server) == {
        "method": "PATCH",
        "path": f"{W}/split-segments",
        "query": {},
        "body": {"patch": ops},
    }
    assert schema("SegmentsPatch")["required"] == ["patch"]


async def test_segment_update_refuses_an_empty_patch(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`patch` must be a non-empty list"):
        await client.workspace.segment_update([])
    assert server.requests == []


# --- workspace users ----------------------------------------------------------------------------


async def test_user_add_posts_the_invite_envelope(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.user_add(["a@x.io"])
    projects = [{"project_id": 1, "role": "project_analyst"}]
    await client.workspace.user_add(["a@x.io", "b@x.io"], projects=projects)
    assert [r["body"] for r in server.requests] == [
        {"invite": {"email_ids": ["a@x.io"]}},
        {"invite": {"email_ids": ["a@x.io", "b@x.io"], "projects": projects}},
    ]
    assert all(r["method"] == "POST" and r["path"] == f"{W}/users" for r in server.requests)
    assert schema("UserInvitePost")["required"] == ["invite"]
    assert schema("UserInviteSchema")["required"] == ["email_ids"]


async def test_user_add_needs_emails(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`email_ids` must be a non-empty list"):
        await client.workspace.user_add([])
    assert server.requests == []


async def test_user_remove_deletes_by_user_id_in_the_path(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.user_remove(12)
    assert _only(server) == {
        "method": "DELETE",
        "path": f"{W}/users/12",
        "query": {},
        "body": None,
    }


@pytest.mark.parametrize("user_id", [0, -3])
async def test_user_remove_refuses_non_positive_ids(
    user_id: int, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=f"positive integer, got {user_id}"):
        await client.workspace.user_remove(user_id)
    assert server.requests == []


async def test_user_remove_batch_sends_ids_and_invite_ids_as_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.user_remove_batch(ids="1,2")
    await client.workspace.user_remove_batch(invite_ids="7")
    await client.workspace.user_remove_batch()
    assert [r["query"] for r in server.requests] == [{"ids": "1,2"}, {"invite_ids": "7"}, {}]
    assert all(r["method"] == "DELETE" and r["path"] == f"{W}/users" for r in server.requests)
    assert {"ids", "invite_ids"} <= _declared("/workspaces/{workspace_id}/users", "delete")


async def test_user_update_batch_wraps_patches_and_refuses_none(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    example = schema("WorkspaceUsersPatch")["examples"][2]
    await client.workspace.user_update_batch(example["patches"])
    assert _only(server) == {"method": "PATCH", "path": f"{W}/users", "query": {}, "body": example}
    server.requests.clear()
    with pytest.raises(MammothValidationError, match="`patches` must be a non-empty list"):
        await client.workspace.user_update_batch([])
    assert server.requests == []


# --- invites (all go through the users routes) --------------------------------------------------


async def test_invite_list_asks_for_invited_users_and_returns_only_the_invites(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {W}/users"] = {"users": [{"id": 1}], "invites": [{"invite_id": 4}]}
    assert await client.workspace.invite_list() == {"invites": [{"invite_id": 4}]}
    assert _only(server)["query"] == {"invited": "true", "limit": "1"}
    assert {"invited", "limit", "project_id"} <= _declared(
        "/workspaces/{workspace_id}/users", "get"
    )


async def test_invite_list_filters_by_project_and_tolerates_a_missing_key(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {W}/users"] = {"users": []}
    assert await client.workspace.invite_list(project_id=9) == {"invites": []}
    assert _only(server)["query"] == {"invited": "true", "limit": "1", "project_id": "9"}


async def test_invite_resend_and_revoke_use_the_spec_patch_commands(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.invite_resend([1, 2, 3])
    await client.workspace.invite_revoke(["4"])
    assert [r["body"] for r in server.requests] == [
        {"patches": [{"op": "command", "path": "invite_resend", "value": "1,2,3"}]},
        {"patches": [{"op": "remove", "path": "invite", "value": "4"}]},
    ]
    assert all(r["method"] == "PATCH" and r["path"] == f"{W}/users" for r in server.requests)
    paths = schema("WorkspaceUsersPatchPatchPaths")["enum"]
    ops = schema("WorkspaceUsersPatchPatchOps")["enum"]
    for r in server.requests:
        patch = r["body"]["patches"][0]
        assert patch["path"] in paths and patch["op"] in ops


async def test_invite_role_update_sends_the_update_user_roles_value(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.invite_role_update(5, "workspace_member")
    assert _only(server)["body"] == {
        "patches": [
            {
                "op": "replace",
                "path": "invite_role",
                "value": {"invite_id": 5, "new_role": "workspace_member"},
            }
        ]
    }
    assert {"invite_id", "new_role"} <= set(schema("UpdateUserRoles")["properties"])


@pytest.mark.parametrize(
    ("invite_id", "role", "message"),
    [
        (0, "r", "invite ids must be positive integers, got 0"),
        (True, "r", "invite ids must be positive integers, got True"),
        (3, "", "`role` must be a non-empty string"),
    ],
)
async def test_invite_role_update_validates_before_any_request(
    invite_id: Any,
    role: str,
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.workspace.invite_role_update(invite_id, role)
    assert server.requests == []


async def test_invite_delete_removes_by_invite_ids_query(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.invite_delete([8, 9])
    assert _only(server) == {
        "method": "DELETE",
        "path": f"{W}/users",
        "query": {"invite_ids": "8,9"},
        "body": None,
    }


@pytest.mark.parametrize(
    ("ids", "message"),
    [
        ([], "`invite_ids` must be a non-empty list"),
        ([1, 0], "invite ids must be positive integers, got 0"),
        ([True], "invite ids must be positive integers, got True"),
        (["x"], "invite ids must be positive integers, got 'x'"),
        ([-2], "invite ids must be positive integers, got -2"),
    ],
)
@pytest.mark.parametrize("method", ["invite_resend", "invite_revoke", "invite_delete"])
async def test_invite_id_lists_are_validated_before_any_request(
    method: str,
    ids: list[Any],
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await getattr(client.workspace, method)(ids)
    assert server.requests == []


# --- accept invite, create, AI helpers, usage ----------------------------------------------------


async def test_accept_invite_posts_the_token_to_the_unscoped_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.accept_invite("tok_1")
    assert _only(server) == {
        "method": "POST",
        "path": "/accept-invite",
        "query": {},
        "body": {"token": "tok_1"},
    }
    assert schema("AcceptInviteSchema")["required"] == ["token"]


async def test_accept_invite_refuses_an_empty_token(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`token` must be a non-empty string"):
        await client.workspace.accept_invite("")
    assert server.requests == []


async def test_create_posts_the_body_to_workspaces(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.create({"name": "Acme"})
    assert _only(server) == {
        "method": "POST",
        "path": "/workspaces",
        "query": {},
        "body": {"name": "Acme"},
    }


async def test_check_expression_posts_to_the_ai_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.check_expression({"intent": "sum of a and b"})
    assert _only(server) == {
        "method": "POST",
        "path": f"{W}/ai/check-expression",
        "query": {},
        "body": {"intent": "sum of a and b"},
    }


async def test_llm_task_names_the_type_and_params_as_the_spec_does(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.llm_task("rename_columns", {"columns": ["a"]})
    assert _only(server) == {
        "method": "POST",
        "path": f"{W}/llm",
        "query": {},
        "body": {"type": "rename_columns", "params": {"columns": ["a"]}},
    }
    assert set(schema("UnifiedLlmTaskSpec")["required"]) == {"type", "params"}


async def test_llm_task_refuses_an_empty_type(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="`task_type` must be a non-empty string"):
        await client.workspace.llm_task("", {})
    assert server.requests == []


async def test_app_usage_sends_fields_only_when_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workspace.app_usage()
    await client.workspace.app_usage(fields="a,b")
    assert [(r["path"], r["query"]) for r in server.requests] == [
        (f"{W}/app-usage", {}),
        (f"{W}/app-usage", {"fields": "a,b"}),
    ]
    assert "fields" in _declared("/workspaces/{workspace_id}/app-usage", "get")
