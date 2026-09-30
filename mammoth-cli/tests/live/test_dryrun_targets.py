"""Live: ``--dry-run`` names what a destructive command would change.

Every case runs the real CLI against a real backend. A scratch project is
filled with real resources (uploaded files and their datasets and batches,
views, folders, a parameter, a snippet, a webhook, a workflow, a dashboard);
each destructive command is then dry-run and its ``targets`` are compared with the names
the resources were created with. The resources are
deleted at the end, and a dry run is checked to have deleted nothing.

Credentials come from the shared ``login`` fixture in ``conftest.py``:
``MAMMOTH_LIVE_LOGIN_FACTORY`` (``module:callable`` returning an
:class:`~mammoth_cli.context.resolver.ExplicitLogin`) when set, else the
key/secret variables; the suite skips without either. Run it on the box that has the test identity::

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_dryrun_targets.py -m live -v
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli import embed
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.dryrun_targets import (
    CODE_TARGETS_UNRESOLVABLE,
    COMMAND_TARGETS,
    SUBS,
)

pytestmark = pytest.mark.live

PREFIX = "dryrun-targets"
_QUIET = ["--no-input"]
_YES = ["--yes", "--no-input"]


@dataclass
class World:
    """The scratch resources and the names they were created with."""

    login: ExplicitLogin
    project: int = 0
    spare_projects: list[int] = field(default_factory=list)
    names: dict[str, str] = field(default_factory=dict)
    ids: dict[str, int] = field(default_factory=dict)

    def run(self, *args: str, scoped: bool = True) -> dict[str, Any]:
        """Run ``mammoth <args>`` (in the scratch project) and return the envelope."""
        project_id = self.project if scoped else None
        return embed.invoke(list(args), login=self.login, project_id=project_id)

    def ok(self, *args: str, scoped: bool = True) -> dict[str, Any]:
        envelope = self.run(*args, scoped=scoped)
        for _ in range(2):  # koyal answers 502/504 under load; a scratch duplicate is harmless
            if envelope.get("error", {}).get("code") not in ("outcome_unknown", "retryable_error"):
                break
            time.sleep(15)
            envelope = self.run(*args, scoped=scoped)
        assert "error" not in envelope, f"{' '.join(args)}: {envelope.get('error')}"
        data: dict[str, Any] = envelope["data"]
        return data

    def dry(self, *args: str) -> dict[str, Any]:
        """Dry-run ``args``, returning the envelope."""
        return self.run(*args, "--dry-run", *_QUIET)


def _create_project(world: World, name: str) -> int:
    data = world.ok("project", "create", name, *_YES, scoped=False)
    return int(data["id"])


def _upload(world: World, tmp: Path, stem: str) -> None:
    path = tmp / f"{stem}.csv"
    path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    data = world.ok("file", "upload", str(path), *_YES)
    world.ids[f"ds_{stem}"] = int(data["dataset_id"])
    world.names[f"ds_{stem}"] = path.name
    files = world.ok("file", "list")["files"]
    world.ids[f"file_{stem}"] = next(f["id"] for f in files if f["name"] == path.name)
    world.names[f"file_{stem}"] = path.name
    dataset_id = world.ids[f"ds_{stem}"]
    batches = world.ok("batch", "list", str(dataset_id))["batches"]
    world.ids[f"batch_{stem}"] = batches[0]["id"]
    world.names[f"batch_{stem}"] = batches[0]["name"]


def _build(world: World, tmp: Path, stamp: int) -> None:
    for stem in (f"dta_{stamp}", f"dtb_{stamp}"):
        _upload(world, tmp, stem)
    a = world.ids[f"ds_dta_{stamp}"]
    world.ids["view"] = int(world.ok("view", "create", str(a), *_YES)["id"])
    world.ids["view2"] = int(world.ok("view", "create", str(a), *_YES)["id"])
    views = world.ok("view", "list", "--input", json.dumps({"dataset_id": a}))["dataviews"]
    by_id = {v["id"]: v["name"] for v in views}
    world.names["view"], world.names["view2"] = by_id[world.ids["view"]], by_id[world.ids["view2"]]
    for key, command, extra in (
        ("folder", ("folder", "create"), []),
        ("folder2", ("folder", "create"), []),
        ("parameter", ("parameter", "create"), ["--input", '{"param_type": "TEXT", "value": "x"}']),
        ("snippet", ("snippet", "create"), ["--input", '{"code": "1", "language": "python"}']),
        ("webhook", ("webhook", "create"), []),
        ("workflow", ("workflow", "create"), []),
    ):
        name = f"dryrun_{key}_{stamp}"  # parameter names must be identifiers
        data = world.ok(*command, name, *extra, *_YES)
        record = data.get("webhook", data)
        world.ids[key], world.names[key] = int(record["id"]), name
    _build_view_parts(world, a)
    made = world.ok(
        *("dashboard", "v3", "generate"),
        *(
            "--input",
            json.dumps(
                {"body": {"params": {"intent": "Row count", "dataview_id": world.ids["view"]}}}
            ),
        ),
        *_YES,
    )
    world.ids["dashboard"] = int(made.get("id") or made["dashboard_id"])
    world.names["dashboard"] = made["state"]["object"]["title"]
    members = world.run("workspace", "user", "list")["data"]
    me = next(u for u in (members if isinstance(members, list) else members["users"]) if u["email"])
    world.ids["user"] = int(me["id"])
    world.names["user"] = f"{me['first_name']} {me['last_name']}".strip()


def _first(world: World, args: tuple[str, ...], key: str, label: str) -> tuple[Any, str] | None:
    """The first item of an existing list read: (id, label), or None when empty."""
    data = world.ok(*args)
    items = data if isinstance(data, list) else data.get(key, [])
    return (items[0]["id"], items[0][label]) if items else None


def _build_view_parts(world: World, dataset: int) -> None:
    """A pipeline step, its version and a draft on real views; a group; spare projects."""
    view = str(world.ids["view"])
    scope = json.dumps({"dataset_id": dataset})
    world.ok(
        "view",
        "transform",
        "limit-rows",
        view,
        "--input",
        json.dumps({"n": 2, "dataset_id": dataset}),
        *_YES,
    )
    tasks = world.ok("view", "task", "list", view, "--input", scope)["tasks"]
    world.ids["task"], world.names["task"] = tasks[0]["id"], "step 1: LIMIT"
    versions = world.ok("view", "version", "list", view, str(dataset))["versions"]
    world.ids["version"], world.names["version"] = versions[0]["id"], versions[0]["name"]
    world.ok("view", "draft", "enter", str(world.ids["view2"]), "--input", scope, *_YES)
    name = f"dryrun_group_{int(time.time())}"
    world.ids["group"], world.names["group"] = (
        int(world.ok("parameter", "group", "create", name, *_YES)["id"]),
        name,
    )
    for key in ("spare1", "spare2"):
        name = f"{PREFIX}-{key}-{int(time.time())}"
        world.ids[key], world.names[key] = _create_project(world, name), name
        world.spare_projects.append(world.ids[key])


def _sweep(world: World) -> None:
    """Delete the scratch projects this run created, by the ids it recorded."""
    for pid in (world.project, *world.spare_projects):
        if pid:
            world.run(
                "project", "delete", str(pid), "--yes", "--confirm", str(pid), *_QUIET, scoped=False
            )


@pytest.fixture(scope="module")
def world(login: ExplicitLogin, tmp_path_factory: pytest.TempPathFactory) -> Iterator[World]:
    stamp = int(time.time())
    scratch = World(login=login)
    scratch.project = _create_project(scratch, f"{PREFIX}-main-{stamp}")
    scratch.names["main"] = f"{PREFIX}-main-{stamp}"
    try:
        _build(scratch, tmp_path_factory.mktemp("dryrun"), stamp)
        yield scratch
    finally:
        _sweep(scratch)


def _stamp(world: World) -> str:
    return world.names["main"].rsplit("-", 1)[1]


def _target(world: World, kind: str, key: str) -> dict[str, Any]:
    return {"type": kind, "id": world.ids[key], "name": world.names[key]}


def _cases(world: World) -> dict[str, tuple[list[str], list[dict[str, Any]]]]:
    s = _stamp(world)
    ds_a, ds_b = f"ds_dta_{s}", f"ds_dtb_{s}"
    file_a, file_b = f"file_dta_{s}", f"file_dtb_{s}"
    batch = f"batch_dta_{s}"
    a, b = world.ids[ds_a], world.ids[ds_b]

    def ids(*keys: str) -> str:
        return json.dumps([world.ids[k] for k in keys])

    return {
        "dataset.delete": (["dataset", "delete", str(a)], [_target(world, "dataset", ds_a)]),
        "dataset.bulk-delete": (
            ["dataset", "bulk-delete", "--input", f'{{"dataset_ids": {ids(ds_a, ds_b)}}}'],
            [_target(world, "dataset", ds_a), _target(world, "dataset", ds_b)],
        ),
        "dataset.file-settings.undo": (
            ["dataset", "file-settings", "undo", str(b)],
            [_target(world, "dataset", ds_b)],
        ),
        "view.delete": (
            ["view", "delete", str(world.ids["view"]), str(a)],
            [_target(world, "view", "view")],
        ),
        "view.bulk-delete": (
            [
                "view",
                "bulk-delete",
                str(a),
                "--input",
                f'{{"dataview_ids": {ids("view", "view2")}}}',
            ],
            [_target(world, "view", "view"), _target(world, "view", "view2")],
        ),
        "batch.delete": (
            ["batch", "delete", str(a), str(world.ids[batch])],
            [_target(world, "batch", batch)],
        ),
        "batch.bulk-delete": (
            ["batch", "bulk-delete", str(a), "--input", f'{{"ids": {ids(batch)}}}'],
            [_target(world, "batch", batch)],
        ),
        "file.delete": (
            ["file", "delete", str(world.ids[file_a])],
            [_target(world, "file", file_a)],
        ),
        "file.bulk-delete": (
            ["file", "bulk-delete", "--input", f'{{"file_ids": {ids(file_a, file_b)}}}'],
            [_target(world, "file", file_a), _target(world, "file", file_b)],
        ),
        "folder.delete": (
            ["folder", "delete", str(world.ids["folder"])],
            [_target(world, "folder", "folder")],
        ),
        "folder.bulk-delete": (
            ["folder", "bulk-delete", "--input", f'{{"folder_ids": {ids("folder", "folder2")}}}'],
            [_target(world, "folder", "folder"), _target(world, "folder", "folder2")],
        ),
        "webhook.delete": (
            ["webhook", "delete", str(world.ids["webhook"])],
            [_target(world, "webhook", "webhook")],
        ),
        "parameter.delete": (
            ["parameter", "delete", str(world.ids["parameter"])],
            [_target(world, "parameter", "parameter")],
        ),
        "snippet.delete": (
            ["snippet", "delete", str(world.ids["snippet"])],
            [_target(world, "snippet", "snippet")],
        ),
        "workflow.delete": (
            ["workflow", "delete", str(world.ids["workflow"])],
            [_target(world, "workflow", "workflow")],
        ),
        "view.task.delete": (
            [
                "view",
                "task",
                "delete",
                str(world.ids["view"]),
                str(world.ids["task"]),
                "--input",
                json.dumps({"dataset_id": a}),
            ],
            [
                {
                    "type": "step",
                    "id": world.ids["task"],
                    "name": (
                        f"\u201c{world.names['view']}\u201d \u203a step "
                        f"\u201c{world.names['task'][5:]}\u201d"
                    ),
                }
            ],
        ),
        "view.version.delete": (
            [
                "view",
                "version",
                "delete",
                str(world.ids["view"]),
                str(world.ids["version"]),
                str(a),
            ],
            [
                {
                    "type": "version",
                    "id": world.ids["version"],
                    "name": (
                        f"\u201c{world.names['view']}\u201d \u203a version "
                        f"\u201c{world.names['version']}\u201d"
                    ),
                }
            ],
        ),
        "view.draft.discard": (
            [
                "view",
                "draft",
                "discard",
                str(world.ids["view2"]),
                "--input",
                json.dumps({"dataset_id": a}),
            ],
            [
                {
                    "type": "draft",
                    "id": world.ids["view2"],
                    "name": f"\u201c{world.names['view2']}\u201d \u203a unsaved draft changes",
                }
            ],
        ),
        "parameter.group.delete": (
            ["parameter", "group", "delete", str(world.ids["group"])],
            [
                {
                    "type": "parameter group",
                    "id": world.ids["group"],
                    "name": f"parameter group \u201c{world.names['group']}\u201d",
                }
            ],
        ),
        "project.delete": (
            ["project", "delete", str(world.ids["spare1"])],
            [_target(world, "project", "spare1")],
        ),
        "project.bulk-delete": (
            ["project", "bulk-delete", "--input", f'{{"project_ids": {ids("spare1", "spare2")}}}'],
            [_target(world, "project", "spare1"), _target(world, "project", "spare2")],
        ),
        "dashboard.delete": (
            ["dashboard", "delete", str(world.ids["dashboard"])],
            [_target(world, "dashboard", "dashboard")],
        ),
        "workspace.user.remove": (
            ["workspace", "user", "remove", str(world.ids["user"])],
            [_target(world, "user", "user")],
        ),
        "workspace.user.remove-batch": (
            ["workspace", "user", "remove-batch", "--input", f'{{"ids": "{world.ids["user"]}"}}'],
            [_target(world, "user", "user")],
        ),
    }


CASE_IDS = [
    "dataset.delete",
    "dataset.bulk-delete",
    "dataset.file-settings.undo",
    "view.delete",
    "view.bulk-delete",
    "batch.delete",
    "batch.bulk-delete",
    "file.delete",
    "file.bulk-delete",
    "folder.delete",
    "folder.bulk-delete",
    "webhook.delete",
    "parameter.delete",
    "snippet.delete",
    "workflow.delete",
    "dashboard.delete",
    "workspace.user.remove",
    "workspace.user.remove-batch",
    "view.task.delete",
    "view.version.delete",
    "view.draft.discard",
    "parameter.group.delete",
    "project.delete",
    "project.bulk-delete",
]


@pytest.mark.parametrize("command_id", CASE_IDS)
def test_dry_run_names_every_target(world: World, command_id: str) -> None:
    argv, expected = _cases(world)[command_id]
    envelope = world.dry(*argv)
    assert "error" not in envelope, envelope.get("error")
    data = envelope["data"]
    assert data["dry_run"] is True
    manifest_class = next(r for r in load_commands() if r["command_id"] == command_id)
    assert data["mutation_class"] == manifest_class["mutation_class"]
    assert data["irreversible"] is (data["mutation_class"] == "destructive")
    assert data["targets"] == expected


def test_a_dry_run_deletes_nothing(world: World) -> None:
    s = _stamp(world)
    dataset_id = world.ids[f"ds_dta_{s}"]
    world.dry("dataset", "delete", str(dataset_id))
    listed = world.ok("dataset", "list")["datasets"]
    assert dataset_id in [d["id"] for d in listed]


def test_an_unknown_id_fails_loud_with_no_targets(world: World) -> None:
    envelope = world.dry("dataset", "delete", "987654321")
    assert "error" in envelope
    assert "data" not in envelope
    assert envelope["error"]["code"]
    assert envelope["error"]["hint"]


MAPPED = set(COMMAND_TARGETS) | set(SUBS) | {"user.avatar.delete"}


def test_every_destructive_command_has_a_reader() -> None:
    destructive = {r["command_id"] for r in load_commands() if r["mutation_class"] == "destructive"}
    assert destructive - MAPPED == set()


def test_the_only_unnameable_destructive_call_is_a_filter_selection() -> None:
    """`notification delete-batch` without ids deletes by filter: no target list exists."""
    # Exercised live below (test_a_filter_selection_fails_loud); nothing else may be unnameable.
    assert "notification.delete-batch" in SUBS


def _not_set_up_live() -> list[str]:
    return sorted(MAPPED - set(CASE_IDS))


@pytest.mark.parametrize("command_id", _not_set_up_live())
def test_a_command_without_live_setup_names_or_fails_loud(world: World, command_id: str) -> None:
    """Dummy ids from the manifest example: the dry run names them or errors, never `[]`."""
    record = next(r for r in load_commands() if r["command_id"] == command_id)
    envelope = world.dry(*_example_argv(str(record.get("agent_example") or "")))
    if "error" in envelope:
        assert envelope["error"]["code"]
        return
    targets = envelope["data"]["targets"]
    assert targets
    assert all(t["name"] for t in targets)


def test_a_filter_selection_fails_loud(world: World) -> None:
    envelope = world.dry("notification", "delete-batch", "--input", '{"is_read": true}')
    assert envelope["error"]["code"] == CODE_TARGETS_UNRESOLVABLE


def _example_argv(example: str) -> list[str]:
    import shlex

    argv = shlex.split(example)[1:]
    return [part for part in argv if part not in ("--yes",)]
