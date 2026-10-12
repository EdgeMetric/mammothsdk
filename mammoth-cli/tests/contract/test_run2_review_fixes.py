"""Run-2 review fixes through the real CLI handlers and SDK, faking only the HTTP wire.

Uses the ``real_service`` fixture: the handler, the SDK service and the SDK
sub-clients run for real; only the transport is the repo's recording ``FakeApi``.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands import dataset as dataset_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

_CANVAS = r"/dashboards/7/canvas"


@contextmanager
def _bind(monkeypatch: pytest.MonkeyPatch, module: Any, service: Any):
    @contextmanager
    def context(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(module, "open_service", context)
    yield


def _input(tmp_path: Path, payload: dict[str, Any]) -> str:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _rate_board_canvas() -> dict[str, Any]:
    return {
        "canvas": {
            "dataset": {"dataview_id": 42},
            "focus": {"kpis": [{"label": "On-time delivery rate", "field": "id", "agg": "count"}]},
        }
    }


def test_share_confirmation_names_a_count_titled_as_a_rate_and_the_unpublished_board(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    api.on("GET", r"/dashboards/7$", body={"id": 7, "was_published": False})
    api.on("GET", _CANVAS, body=_rate_board_canvas())
    with _bind(monkeypatch, dashboard_cmd, service), pytest.raises(CliError) as caught:
        dashboard_cmd.dashboard_share(
            Invocation(
                "dashboard.share",
                output="json",
                no_input=True,
                extra_args=["7"],
                input_file=_input(tmp_path, {"type_of_auth": "public"}),
            )
        )
    assert caught.value.code == "confirmation_required"
    assert "shows a count, title reads as a rate" in caught.value.message
    assert "not published yet" in caught.value.message
    assert not any(r.method == "POST" for r in api.requests)


def test_publish_data_on_a_never_published_board_publishes_the_presentation(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    api.on("GET", r"/dashboards/7$", body={"id": 7, "was_published": False})
    api.on("GET", _CANVAS, body={"canvas": {"dataset": {}}})
    with _bind(monkeypatch, dashboard_cmd, service):
        data, _meta = dashboard_cmd.dashboard_action(
            Invocation(
                "dashboard.action",
                output="json",
                no_input=True,
                yes=True,
                extra_args=["7"],
                input_file=_input(tmp_path, {"action": "publish-data"}),
            )
        )
    (post,) = [r for r in api.requests if r.method == "POST"]
    assert post.path.endswith("/dashboards/7/action")
    assert post.json_body["action"] == "publish-presentation"
    assert data["action"] == "publish-presentation"


def test_publish_data_on_a_published_board_stays_publish_data(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    api.on("GET", r"/dashboards/7$", body={"id": 7, "was_published": True})
    api.on("GET", _CANVAS, body={"canvas": {"dataset": {}}})
    with _bind(monkeypatch, dashboard_cmd, service):
        dashboard_cmd.dashboard_action(
            Invocation(
                "dashboard.action",
                output="json",
                no_input=True,
                yes=True,
                extra_args=["7"],
                input_file=_input(tmp_path, {"action": "publish-data"}),
            )
        )
    (post,) = [r for r in api.requests if r.method == "POST"]
    assert post.json_body["action"] == "publish-data"


def test_schema_diff_proposes_the_mapping_batch_create_takes(
    real_service: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, api = real_service(project_id=3)
    destination = [
        {"c_name": "id", "c_id": "c1", "c_type": "NUMERIC"},
        {"c_name": "hub", "c_id": "c2", "c_type": "TEXT"},
        {"c_name": "legacy", "c_id": "c3", "c_type": "TEXT"},
    ]
    source = [
        {"c_name": "id", "c_id": "s1", "c_type": "NUMERIC"},
        {"c_name": "warehouse", "c_id": "s2", "c_type": "TEXT"},
        {"c_name": "extra", "c_id": "s3", "c_type": "NUMERIC"},
    ]
    api.on("GET", r"/datasets/10$", body={"dataset": {"data_schema": destination}})
    api.on("GET", r"/datasets/11$", body={"dataset": {"data_schema": source}})
    api.on(
        "GET",
        r"/datasets/10/data$",
        body={
            "data": {"1": ["1", "Zaragoza", "x"], "2": ["2", "Madrid", None]},
            "headers": ["id", "hub", "legacy"],
            "limit": 100,
            "offset": 0,
        },
    )
    api.on(
        "GET",
        r"/datasets/11/data$",
        body={
            "data": {"1": ["3", "Zaragoza", "5"]},
            "headers": ["id", "warehouse", "extra"],
            "limit": 100,
            "offset": 0,
        },
    )
    with _bind(monkeypatch, dataset_cmd, service):
        data, _meta = dataset_cmd.dataset_schema_diff(
            Invocation(
                "dataset.schema-diff",
                output="json",
                no_input=True,
                project=3,
                extra_args=["10", "11"],
            )
        )
    assert data["mapping"] == [
        {"source_c_name": "id", "destination_c_name": "id"},
        {"source_c_name": "warehouse", "destination_c_name": "hub"},
    ]
    assert data["added"] == [{"c_name": "extra", "c_type": "NUMERIC"}]
    assert data["removed"] == [{"c_name": "legacy", "c_type": "TEXT"}]
    assert data["renamed"][0]["shared_values"] == ["Zaragoza"]


# C7: notes in a free-text column, counted per quarter (the bucket the CLI asks for).
# "cutover" is in 156 notes in Q3 against 16 in Q2; every other word grew by less.
_NOTES = [
    ("cutover scheduled for friday night", {"2026-04-01": 4, "2026-07-01": 52}),
    ("cutover rehearsal failed twice", {"2026-04-01": 3, "2026-07-01": 52}),
    ("waiting on cutover sign off", {"2026-04-01": 9, "2026-07-01": 52}),
    ("invoice reminder sent again", {"2026-04-01": 55, "2026-07-01": 58}),
]


def test_drivers_names_the_term_that_grew_in_a_free_text_column(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from mammoth_cli.commands import view_drivers

    service, api = real_service(project_id=3)
    metadata = [
        {"internal_name": "column_1", "display_name": "note", "type": "TEXT"},
        {"internal_name": "column_2", "display_name": "logged", "type": "DATE"},
    ]
    api.on("GET", r"/dataviews/9$", body={"metadata": metadata, "dataset_id": 7})

    def aggregate(request: Any) -> tuple[int, Any]:
        if not request.json_body["param"]["PIVOT"].get("GROUP_BY"):
            return 200, {"data": [{"agg_0": "2026-04-01", "agg_1": "2026-09-30"}]}
        return 200, {
            "data": [
                {"group_0": note, "group_1": quarter, "agg_0": count}
                for note, quarters in _NOTES
                for quarter, count in quarters.items()
            ]
        }

    api.on("POST", r"/data/query$", handler=aggregate)
    document = {
        "measure": {"function": "COUNT"},
        "date_column": "logged",
        "compare": ["2026-Q2", "2026-Q3"],
        "by": ["note"],
    }
    with _bind(monkeypatch, view_drivers, service):
        result, _meta = view_drivers.view_data_drivers(
            Invocation(
                "view.data.drivers",
                output="json",
                no_input=True,
                project=3,
                extra_args=["9", "7"],
                input_file=_input(tmp_path, document),
            )
        )
    terms = result["contributors"]["note"]["terms"]
    assert terms[0] == {"term": "cutover", "count_a": 16, "count_b": 156}
    assert "invoice" not in [t["term"] for t in terms]
