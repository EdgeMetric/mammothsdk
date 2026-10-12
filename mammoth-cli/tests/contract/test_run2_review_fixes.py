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
from mammoth_cli.commands import view_drivers
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.period_analysis import parse_measure, parse_period
from mammoth_cli.services.schema_diff import column_samples, schema_diff

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


def test_schema_diff_proposes_the_mapping_batch_create_takes() -> None:
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
    # The `dataset data` read as koyal returns it (workspace 4, dataset 326): rows keyed by
    # row number, each a list in `headers` order.
    destination_read = {
        "data": {"1": ["1", "Zaragoza", "x"], "2": ["2", "Madrid", None]},
        "headers": ["id", "hub", "legacy"],
        "limit": 100,
        "offset": 0,
    }
    source_read = {
        "data": {"1": ["3", "Zaragoza", "5"]},
        "headers": ["id", "warehouse", "extra"],
        "limit": 100,
        "offset": 0,
    }
    data = schema_diff(
        destination,
        source,
        column_samples(destination_read, destination),
        column_samples(source_read, source),
    )
    assert data["mapping"] == [
        {"source_c_name": "id", "destination_c_name": "id"},
        {"source_c_name": "warehouse", "destination_c_name": "hub"},
    ]
    assert data["added"] == [{"c_name": "extra", "c_type": "NUMERIC"}]
    assert data["removed"] == [{"c_name": "legacy", "c_type": "TEXT"}]
    assert data["renamed"][0]["shared_values"] == ["Zaragoza"]


# C7: notes counted per quarter, as `view data aggregate` returns them (koyal, view 878):
# {"STATUS": "READY", "data": [{"<as_name>": 10.0, "<column>": "..."}], "metadata": [...]}.
# "cutover" is in 156 notes in Q3 against 16 in Q2; every other word grew by less.
_NOTES = [
    ("cutover scheduled for friday night", {"2026-04-01": 4.0, "2026-07-01": 52.0}),
    ("cutover rehearsal failed twice", {"2026-04-01": 3.0, "2026-07-01": 52.0}),
    ("waiting on cutover sign off", {"2026-04-01": 9.0, "2026-07-01": 52.0}),
    ("invoice reminder sent again", {"2026-04-01": 55.0, "2026-07-01": 58.0}),
]


def test_drivers_names_the_term_that_grew_in_a_free_text_column() -> None:
    read = {
        "STATUS": "READY",
        "data": [
            {"note": note, "logged": quarter, "__rows": count}
            for note, quarters in _NOTES
            for quarter, count in quarters.items()
        ],
        "metadata": [],
    }
    measure = parse_measure({"function": "SUM", "column": "revenue"}, ("SUM",))
    periods = [parse_period("2026-Q2"), parse_period("2026-Q3")]

    assert view_drivers._is_free_text(read, "note")
    terms = view_drivers._terms(read, measure, "logged", "note", periods)

    assert terms[0] == {"term": "cutover", "count_a": 16, "count_b": 156}
    assert "invoice" not in [t["term"] for t in terms]
