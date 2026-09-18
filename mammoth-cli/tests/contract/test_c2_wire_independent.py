"""Independent C2 wire oracles for the S2 and S6 route families.

The expected requests live in ``fixtures/C2-CROSS-FAMILY-WIRE.json`` and are
written from the pinned OpenAPI surface.  This test intentionally calls the
real SDK API methods with a recording client; it does not use CLI command
contracts, handler metadata, or SDK introspection to build expected values.

This is a high-value pilot, not a claim that every S2/S6 route is closed.  The
fixture carries the route-count denominator and the workbook result records
the uncovered route IDs.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from mammoth.api.addons import AddonsAPI
from mammoth.api.annotations import AnnotationsAPI
from mammoth.api.browse import BrowseAPI
from mammoth.api.dashboards import DashboardActionType, DashboardsAPI
from mammoth.api.data_apps import DataAppsAPI
from mammoth.api.datasets import DatasetsAPI
from mammoth.api.files import FilesAPI
from mammoth.api.notifications import NotificationsAPI
from mammoth.api.projects import ProjectsAPI
from mammoth.api.reports import ReportsAPI
from mammoth.api.templates import TemplatesAPI
from mammoth.api.trash import TrashAPI
from pydantic import ValidationError

FIXTURE = Path(__file__).with_name("fixtures") / "C2-CROSS-FAMILY-WIRE.json"


class RecordingClient:
    """Small transport seam used by real SDK resource methods."""

    workspace_id = 17
    project_id = 41
    job_timeout = 0

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((method, path, kwargs))
        # Enough shape for the one list wrapper that is used below.  Generated
        # methods may reject this deliberately minimal response after they have
        # emitted their request; the oracle still verifies the captured wire.
        if path == "/dashboards":
            return {"dashboards": []}
        return {}

    def _request_list(self, method: str, path: str, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append((method, path, kwargs))
        return []

    def _wait_if_job(self, response: dict[str, Any], **_: Any) -> dict[str, Any]:
        return response


def _fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _invoke(client: RecordingClient, route: str) -> None:
    projects = ProjectsAPI(client)  # type: ignore[arg-type]
    datasets = DatasetsAPI(client)  # type: ignore[arg-type]
    dashboards = DashboardsAPI(client)  # type: ignore[arg-type]
    # These values are deliberately distinctive and are mirrored only in the
    # independent fixture, never generated from the call below.
    calls: dict[str, Callable[[], Any]] = {
        "project.list": lambda: projects.list(workspace_id=17, limit=13),
        "project.create": lambda: projects.create("C2_PROJECT", "#C20001", "only_me", 17),
        "project.update": lambda: projects.update(41, "C2_RENAMED", "#C20002", 17),
        "project.user.add": lambda: projects.add_users(
            41, ["c2-user@example.invalid"], "editor", 17
        ),
        "project.delete": lambda: projects.delete(41, 17),
        "dataset.list": lambda: datasets.list(17, 41, 19, 7, "C2_SORT"),
        "dataset.create": lambda: datasets.create(
            {"name": "C2_DATASET", "url": "https://example.invalid/data.csv"},
            "weburl",
            "C2_FOLDER",
            17,
            41,
        ),
        "dataset.update": lambda: datasets.update(
            [{"op": "replace", "path": "/41/name", "value": {"name": "C2_UPDATED"}}],
            17,
            41,
        ),
        "dataset.data": lambda: datasets.get_data(41, 17, 41),
        "browse.root": lambda: BrowseAPI(client).root(
            name="C2_BROWSE", limit=23, include_hidden=True
        ),  # type: ignore[arg-type]
        "annotation.create": lambda: AnnotationsAPI(client).create(
            "dataset", 41, "C2_ANNOTATION", 41
        ),  # type: ignore[arg-type]
        "addon.connector.add": lambda: AddonsAPI(client).add_connector(connector_ids=[601, 602]),  # type: ignore[arg-type]
        "notification.update": lambda: NotificationsAPI(client).update(
            701, [{"op": "replace", "path": "isRead", "value": False}]
        ),  # type: ignore[arg-type]
        "trash.add": lambda: TrashAPI(client).add([{"id": 801, "type": "dataset"}], 41),  # type: ignore[arg-type]
        "file.list": lambda: FilesAPI(client).list(
            fields="C2_FIELDS",
            file_ids=[901, 902],
            names=["C2_A", "C2_B"],
            statuses=["ready"],
            created_at="C2_CREATED",
            updated_at="C2_UPDATED",
            limit=29,
            offset=3,
            sort="C2_SORT",
        ),  # type: ignore[arg-type]
        "dashboard.list": lambda: dashboards.list(project_id=41),
        "dashboard.create": lambda: dashboards.create(
            "C2 dashboard intent", [1001, 1002], False, True
        ),
        "dashboard.analytics": lambda: dashboards.get_analytics(1001),
        "dashboard.action": lambda: dashboards.action(
            1001, DashboardActionType.AUTO_SYNC, False, 1002
        ),
        "dashboard.data.draft": lambda: dashboards.get_draft_data(
            1001, "c2000000-0000-4000-8000-000000000001"
        ),
        "dashboard.widget-data": lambda: dashboards.widget_data(
            1001, {"params": {"widget_ids": [1003], "C2": "C2_VALUE"}}
        ),
        "dashboard.canvas.get": lambda: dashboards.canvas_get(1001, 7),
        "dashboard.rls.value.list": lambda: dashboards.rls_value_list(
            1001, "C2_COLUMN", "C2_SEARCH"
        ),
        "dashboard.query": lambda: dashboards.query(1001, {"descriptor": "C2_DESCRIPTOR"}),
        "dashboard.context.delete": lambda: dashboards.context_delete("C2_CONTEXT"),
        "dashboard.style.token.list": lambda: dashboards.style_token_list("C2_STYLE"),
        "dashboard.template.list": lambda: dashboards.template_list(),
        "data-app.list": lambda: DataAppsAPI(client).list(17),  # type: ignore[arg-type]
        "data-app.create": lambda: DataAppsAPI(client).create(
            {"name": "C2_APP", "source_dataview_id": 1002}
        ),  # type: ignore[arg-type]
        "data-app.update": lambda: DataAppsAPI(client).update(1101, {"C2_SETTING": "C2_VALUE"}),  # type: ignore[arg-type]
        "report.list": lambda: ReportsAPI(client).list(31, 5),  # type: ignore[arg-type]
        "template.update": lambda: TemplatesAPI(client).update(1201, {"C2_TEMPLATE": "C2_VALUE"}),  # type: ignore[arg-type]
    }
    try:
        calls[route]()
    except ValidationError:
        # Typed generated APIs validate their response after transport.  The
        # request has already been captured and is the subject of this test.
        pass


def _assert_wire(actual: tuple[str, str, dict[str, Any]], expected: dict[str, Any]) -> None:
    assert actual == (expected["method"], expected["path"], expected["kwargs"])


@pytest.mark.parametrize("case", _fixture()["cases"], ids=lambda case: case["id"])
def test_real_sdk_route_matches_independent_wire_oracle(case: dict[str, Any]) -> None:
    client = RecordingClient()
    _invoke(client, case["route"])
    assert len(client.calls) == 1, f"{case['route']} did not emit exactly one request"
    _assert_wire(client.calls[0], case["expected"])


def test_dropped_field_mutation_is_caught_by_independent_oracle() -> None:
    case = next(item for item in _fixture()["cases"] if item["id"] == "project-create")
    client = RecordingClient()
    _invoke(client, case["route"])
    method, path, kwargs = client.calls[0]
    corrupted = dict(kwargs)
    corrupted["json"] = dict(corrupted["json"])
    corrupted["json"].pop("properties")
    with pytest.raises(AssertionError):
        _assert_wire((method, path, corrupted), case["expected"])


def test_coverage_scope_is_explicit_without_workbook_dependencies() -> None:
    fixture = _fixture()
    covered = set(fixture["covered_route_ids"])
    case_routes = {case["route"] for case in fixture["cases"]}
    assert covered == case_routes
    assert fixture["route_inventory"] == {"s2": 94, "s6": 106, "total": 200}
    assert len(covered) == 32
    assert fixture["route_inventory"]["total"] - len(covered) == 168
