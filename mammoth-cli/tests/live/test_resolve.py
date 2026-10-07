"""Live checks: ``resolve NAME`` and ``dataset find`` answer where a name is, from any project.

The in-product agent runs every call under the project the user last opened. A name
that lives in another project, or that is a dataset and not a project, made it ask the
user instead of saying so. Every object here is named ``uqa-live-`` and is deleted.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_resolve.py -m live -v
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live


@dataclass(frozen=True)
class Twins:
    """Two projects that each hold a dataset of the same name, and the name."""

    stem: str
    dataset_name: str
    project_a: int
    project_b: int
    dataset_a: int
    dataset_b: int


def _create_project(live_cli: LiveCli, name: str) -> int:
    data, _ = live_cli.ok("project", "create", name, "--yes")
    return int(data["id"])


def _upload(live_cli: LiveCli, source: Path, project: int) -> int:
    uploaded, _ = live_cli.ok("file", "upload", str(source), "--yes", project=project)
    return int(uploaded["dataset_id"])


@pytest.fixture(scope="module")
def twins(live_cli: LiveCli, tmp_path_factory: pytest.TempPathFactory) -> Iterator[Twins]:
    stem = f"uqa-live-rs-{int(time.time())}"
    source = tmp_path_factory.mktemp("resolve") / f"{stem}-sales.csv"
    source.write_text("Region,Units\nNorth,1\nSouth,2\n", encoding="utf-8")
    created: list[int] = []
    try:
        for suffix in ("a", "b"):
            created.append(_create_project(live_cli, f"{stem}-{suffix}"))
        datasets = [_upload(live_cli, source, project) for project in created]
        view_input = json.dumps({"name": f"{source.name} view"})
        live_cli.ok(
            *("view", "create", str(datasets[0]), "--yes", "--input", view_input),
            project=created[0],
        )
        yield Twins(stem, source.name, created[0], created[1], datasets[0], datasets[1])
    finally:
        for project in created:
            removed = live_cli.run(
                *("project", "delete", str(project), "--yes", "--confirm", str(project)),
                project=None,
            )
            assert "error" not in removed, f"project {project} not deleted: {removed}"


def _kinds(data: dict[str, Any], kind: str) -> dict[int, dict[str, Any]]:
    return {row["id"]: row for row in data["matches"] if row["kind"] == kind}


def test_find_keeps_other_projects_when_the_project_has_its_own_match(
    live_cli: LiveCli, twins: Twins
) -> None:
    flag = json.dumps({"all_projects": True})
    found, _ = live_cli.ok(
        "dataset", "find", twins.dataset_name, "--input", flag, project=twins.project_b
    )

    by_id = {row["id"]: row for row in found["matches"]}
    assert by_id[twins.dataset_b]["in_project"] is True
    assert by_id[twins.dataset_a]["in_project"] is False
    assert by_id[twins.dataset_a]["project_id"] == twins.project_a
    assert by_id[twins.dataset_a]["project_name"] == f"{twins.stem}-a"
    assert found["matches"][0]["id"] == twins.dataset_b


def test_resolve_a_dataset_name_says_dataset_with_both_projects(
    live_cli: LiveCli, twins: Twins
) -> None:
    flag = json.dumps({"all_projects": True})
    data, _ = live_cli.ok("resolve", twins.dataset_name, "--input", flag, project=twins.project_b)

    assert _kinds(data, "project") == {}
    datasets = _kinds(data, "dataset")
    assert {twins.dataset_a, twins.dataset_b} <= set(datasets)
    assert datasets[twins.dataset_a]["exact"] is True
    assert datasets[twins.dataset_a]["project_id"] == twins.project_a
    assert datasets[twins.dataset_b]["in_project"] is True
    assert datasets[twins.dataset_a]["in_project"] is False
    assert _kinds(data, "view"), "the uploaded dataset's view is not resolved"


def test_resolve_a_project_name_says_project(live_cli: LiveCli, twins: Twins) -> None:
    data, _ = live_cli.ok("resolve", f"{twins.stem}-a")

    projects = _kinds(data, "project")
    assert projects[twins.project_a]["exact"] is True
    assert projects[twins.project_a]["project_name"] == f"{twins.stem}-a"
    assert twins.project_b not in projects
    assert _kinds(data, "dataset") == {}
    assert "is a project" in data["note"]


def test_resolve_a_shared_stem_lists_every_kind(live_cli: LiveCli, twins: Twins) -> None:
    data, _ = live_cli.ok("resolve", twins.stem)

    assert {twins.project_a, twins.project_b} <= set(_kinds(data, "project"))
    assert {twins.dataset_a, twins.dataset_b} <= set(_kinds(data, "dataset"))


def test_resolve_nothing_says_so(live_cli: LiveCli) -> None:
    data, _ = live_cli.ok("resolve", "uqa-live-no-such-name-zz")

    assert data["matches"] == []
    assert "Nothing visible" in data["note"]


def test_resolve_under_a_project_with_the_exact_name_returns_only_that_one(
    live_cli: LiveCli, twins: Twins
) -> None:
    data, _ = live_cli.ok("resolve", twins.dataset_name, project=twins.project_b)

    assert [(r["kind"], r["id"]) for r in data["matches"]] == [("dataset", twins.dataset_b)]
    assert data["elsewhere"] >= 1
    assert "all_projects" in data["note"]


def test_resolve_all_projects_lists_the_copies_elsewhere_too(
    live_cli: LiveCli, twins: Twins
) -> None:
    flag = json.dumps({"all_projects": True})
    data, _ = live_cli.ok("resolve", twins.dataset_name, "--input", flag, project=twins.project_b)

    assert {twins.dataset_a, twins.dataset_b} <= set(_kinds(data, "dataset"))
    assert "elsewhere" not in data


def test_resolve_without_a_project_returns_every_copy(live_cli: LiveCli, twins: Twins) -> None:
    data, _ = live_cli.ok("resolve", twins.dataset_name)

    assert {twins.dataset_a, twins.dataset_b} <= set(_kinds(data, "dataset"))
    assert "elsewhere" not in data


def test_find_under_a_project_with_the_exact_name_returns_only_that_one(
    live_cli: LiveCli, twins: Twins
) -> None:
    found, _ = live_cli.ok("dataset", "find", twins.dataset_name, project=twins.project_b)

    assert [row["id"] for row in found["matches"]] == [twins.dataset_b]
    assert found["elsewhere"] == 1
    assert "all_projects" in found["note"]


def test_find_all_projects_lists_the_copies_elsewhere_too(live_cli: LiveCli, twins: Twins) -> None:
    flag = json.dumps({"all_projects": True})
    found, _ = live_cli.ok(
        "dataset", "find", twins.dataset_name, "--input", flag, project=twins.project_b
    )

    assert {twins.dataset_a, twins.dataset_b} <= {row["id"] for row in found["matches"]}
    assert "elsewhere" not in found
