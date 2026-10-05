"""``--dry-run`` of a data-changing transform reports what it would change.

Real-code: argv through the real handler, service and client, with only the
HTTP socket faked. A transform that would change nothing fails the dry run with
``no_op`` (an error envelope, so the in-product agent's confirmation gate sends
it back to the model before any approval card opens).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]

_VIEW = {
    "id": 3062,
    "name": "Fundraising",
    "row_count": 50,
    "metadata": [
        {"display_name": "Donor", "internal_name": "col_a", "type": "TEXT"},
        {"display_name": "Gift", "internal_name": "col_b", "type": "NUMERIC"},
    ],
}


def _dry_run(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    group_counts: list[int],
    input_doc: dict[str, Any] | None = None,
) -> tuple[Any, Any]:
    service, api = real_service(project_id=180)
    # A fresh service per build, as in production: each command closes its own.
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    api.on("GET", r"/datasets/55/dataviews/3062$", body=_VIEW)
    api.on(
        "POST",
        r"/datasets/55/dataviews/3062/data/query$",
        body={"data": [{"agg_0": n} for n in group_counts]},
    )
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "discard-duplicates",
            "3062",
            "--project",
            "180",
            "--input",
            json.dumps({"dataset_id": 55, **(input_doc or {})}),
            "--dry-run",
            "--output",
            "json",
            "--no-input",
        ]
    )
    return result, api


def test_discard_duplicates_dry_run_with_no_duplicates_is_a_no_op_error(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, api = _dry_run(monkeypatch, real_service, [1, 1, 1])
    error = json.loads(result.output)["error"]
    assert error["code"] == "no_op"
    assert "View 3062 has no exact duplicate rows (50 of 50 checked)" in error["message"]
    assert "nothing to change" in error["message"]
    assert not [r for r in api.requests if r.method == "POST" and r.path.endswith("/tasks")]


def test_discard_duplicates_dry_run_reports_the_rows_it_would_remove(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, _ = _dry_run(monkeypatch, real_service, [3, 2, 1])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["dry_run"] is True
    assert data["predicted_impact"] == {
        "rows_removed": 3,
        "row_count": 50,
        "rows_after": 47,
        "exact": True,
    }


def test_discard_duplicates_dry_run_honours_ignore_columns(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, api = _dry_run(monkeypatch, real_service, [1], {"ignore_columns": ["Gift"]})
    error = json.loads(result.output)["error"]
    assert error["code"] == "no_op"
    assert "ignoring Gift" in error["message"]
    query = [r for r in api.requests if r.path.endswith("/data/query")][0].json_body
    grouped = [item["COLUMN"] for item in query["param"]["PIVOT"]["GROUP_BY"]]
    assert grouped == ["col_a"]


def test_discard_duplicates_dry_run_says_so_when_the_count_could_not_run(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    service, api = real_service(project_id=180)
    # A fresh service per build, as in production: each command closes its own.
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    api.on("GET", r"/datasets/55/dataviews/3062$", body=_VIEW)
    api.on("POST", r"/data/query$", status=500, body={"detail": "boom"})
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "discard-duplicates",
            "3062",
            "--project",
            "180",
            "--input",
            '{"dataset_id": 55}',
            "--dry-run",
            "--output",
            "json",
            "--no-input",
        ]
    )
    assert result.exit_code == 0, result.output
    impact = json.loads(result.output)["data"]["predicted_impact"]
    assert impact["checked"] is False and impact["reason"]


def _run(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    command: str,
    doc: dict[str, Any],
    matching: int,
) -> tuple[Any, Any]:
    """Dry-run ``view transform <command>``; every count read answers ``matching``."""
    service, api = real_service(project_id=180)
    # A fresh service per build, as in production: each command closes its own.
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    api.on("GET", r"/datasets/55/dataviews/3062$", body=_VIEW)
    api.on("POST", r"/data/query$", body={"data": [{"agg_0": matching}]})
    result = make_runner().invoke(
        [
            "view",
            "transform",
            command,
            "3062",
            "--project",
            "180",
            "--input",
            json.dumps({"dataset_id": 55, **doc}),
            "--dry-run",
            "--output",
            "json",
            "--no-input",
        ]
    )
    return result, api


_KEEP_ALL = {"condition": {"column": "Gift", "operator": "GTE", "value": 0}}


def test_filter_that_keeps_every_row_is_a_no_op(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, _ = _run(monkeypatch, real_service, "filter", _KEEP_ALL, matching=50)
    error = json.loads(result.output)["error"]
    assert error["code"] == "no_op" and "keeps all of them" in error["message"]


def test_filter_reports_the_rows_it_would_remove(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, _ = _run(monkeypatch, real_service, "filter", _KEEP_ALL, matching=20)
    impact = json.loads(result.output)["data"]["predicted_impact"]
    assert impact["rows_removed"] == 30 and impact["rows_after"] == 20


def test_remove_filter_matching_nothing_is_a_no_op(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    doc = {**_KEEP_ALL, "filter_type": "REMOVE"}
    result, _ = _run(monkeypatch, real_service, "filter", doc, matching=0)
    assert json.loads(result.output)["error"]["code"] == "no_op"
    result, _ = _run(monkeypatch, real_service, "filter", doc, matching=7)
    assert json.loads(result.output)["data"]["predicted_impact"]["rows_removed"] == 7


_FILL = {"column": "Gift", "direction": "FIRST_VALUE"}


def test_fill_missing_on_a_column_without_blanks_is_a_no_op(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, api = _run(monkeypatch, real_service, "fill-missing", _FILL, matching=0)
    assert json.loads(result.output)["error"]["code"] == "no_op"
    sent = [r for r in api.requests if r.path.endswith("/data/query")][0].json_body
    assert "IS_EMPTY" in json.dumps(sent) and "col_b" in json.dumps(sent)


def test_fill_missing_reports_the_blank_cells(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, _ = _run(monkeypatch, real_service, "fill-missing", _FILL, matching=4)
    impact = json.loads(result.output)["data"]["predicted_impact"]
    assert impact["blank_cells"] == 4


def test_replace_of_text_no_row_holds_is_a_no_op(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    doc = {"columns": ["Donor"], "find": "Acme", "replace": "ACME"}
    result, api = _run(monkeypatch, real_service, "replace", doc, matching=0)
    assert json.loads(result.output)["error"]["code"] == "no_op"
    sent = json.dumps([r for r in api.requests if r.path.endswith("/data/query")][0].json_body)
    assert "ICONTAINS" in sent and "col_a" in sent and "Acme" in sent
    result, _ = _run(monkeypatch, real_service, "replace", doc, matching=6)
    assert json.loads(result.output)["data"]["predicted_impact"]["rows_matching"] == 6


def test_bulk_replace_of_values_no_row_holds_is_a_no_op(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    doc = {"columns": ["Donor"], "mapping": [{"search": ["a", "b"], "replace": "c"}]}
    result, _ = _run(monkeypatch, real_service, "bulk-replace", doc, matching=0)
    assert json.loads(result.output)["error"]["code"] == "no_op"
    result, _ = _run(monkeypatch, real_service, "bulk-replace", doc, matching=3)
    assert json.loads(result.output)["data"]["predicted_impact"]["rows_matching"] == 3


def test_replace_scoped_by_a_condition_counts_only_rows_in_scope(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    doc = {
        "columns": ["Donor"],
        "find": "Acme",
        "replace": "ACME",
        "condition": {"column": "Gift", "operator": "GT", "value": 10},
    }
    result, api = _run(monkeypatch, real_service, "replace", doc, matching=0)
    assert json.loads(result.output)["error"]["code"] == "no_op"
    sent = json.dumps([r for r in api.requests if r.path.endswith("/data/query")][0].json_body)
    assert "ICONTAINS" in sent and "col_b" in sent


def test_real_discard_duplicates_with_none_adds_no_task(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    service, api = real_service(project_id=180)
    # A fresh service per build, as in production: each command closes its own.
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    api.on("GET", r"/datasets/55/dataviews/3062$", body=_VIEW)
    api.on("POST", r"/data/query$", body={"data": [{"agg_0": 1}, {"agg_0": 1}]})
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "discard-duplicates",
            "3062",
            "--project",
            "180",
            "--input",
            '{"dataset_id": 55}',
            "--yes",
            "--output",
            "json",
            "--no-input",
        ]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["status"] == "no_change" and "No task was added" in data["note"]
    assert not [r for r in api.requests if r.method == "POST" and r.path.endswith("/tasks")]


def _run_no_match(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, doc: dict[str, Any]
) -> tuple[Any, Any]:
    """Dry-run a filter no row matches; a grouped read answers the column's values."""
    service, api = real_service(project_id=180)
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    api.on("GET", r"/datasets/55/dataviews/3062$", body=_VIEW)

    def query(request: Any) -> tuple[int, Any]:
        if "GROUP_BY" in json.dumps(request.json_body):
            return 200, {"data": [{"group_0": "Ada", "agg_0": 31}, {"group_0": "Bo", "agg_0": 19}]}
        return 200, {"data": [{"agg_0": 0}]}

    api.on("POST", r"/data/query$", handler=query)
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "filter",
            "3062",
            "--project",
            "180",
            "--input",
            json.dumps({"dataset_id": 55, **doc}),
            "--dry-run",
            "--output",
            "json",
            "--no-input",
        ]
    )
    return result, api


_NO_SUCH_DONOR = {"condition": {"column": "Donor", "operator": "EQ", "value": "Cy"}}


def test_a_filter_no_row_matches_names_the_values_the_column_holds(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    # FB-03: "keep only North" on East/West data; the dry run said only that
    # the view would be left empty, so the agent never named East and West.
    result, _ = _run_no_match(monkeypatch, real_service, _NO_SUCH_DONOR)
    impact = json.loads(result.output)["data"]["predicted_impact"]
    assert impact["rows_after"] == 0
    assert impact["no_row_matches"] == {"column": "Donor", "values": {"Ada": 31, "Bo": 19}}


def test_a_remove_filter_no_row_matches_names_the_values_in_its_no_op(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    doc = {**_NO_SUCH_DONOR, "filter_type": "REMOVE"}
    result, _ = _run_no_match(monkeypatch, real_service, doc)
    error = json.loads(result.output)["error"]
    assert error["code"] == "no_op"
    assert "Donor holds: Ada (31), Bo (19)" in error["message"]
