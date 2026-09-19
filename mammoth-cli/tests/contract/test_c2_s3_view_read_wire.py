"""Independent handler and full-CLI HTTP oracles for the S3 read batch.

The handler tests run the real command handlers and SDK client against the
shared recording HTTP adapter. The runner tests additionally pass through the
Typer parser with ``make_runner().invoke(argv)``. Expected method, path, query,
and body values are literal assertions, not values derived from command
metadata or SDK introspection. This bounded batch does not close S3 or S4.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import session
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

WORKSPACE = 4
DATASET = 731
VIEW = 278
PROJECT = 41


def _input(tmp_path: Path, value: dict[str, Any]) -> str:
    path = tmp_path / "s3-input.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return str(path)


def _invocation(
    command_id: str,
    args: list[str],
    input_file: str | None = None,
) -> Invocation:
    return Invocation(
        command_id,
        output="json",
        project=PROJECT,
        no_input=True,
        extra_args=args,
        input_file=input_file,
    )


@contextmanager
def _bound_service(monkeypatch: pytest.MonkeyPatch, service: Any):
    """Bind a real SDK service to the command handler without network access."""

    @contextmanager
    def context(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 17})()

    monkeypatch.setattr(view_cmd, "open_service", context)
    yield


def _bind_runner_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give the in-process runner deterministic credentials without keyring state."""

    monkeypatch.setattr(
        session,
        "resolve_auth",
        lambda _invocation: ResolvedAuth(
            api_key="k",
            api_secret="s",
            workspace_id=WORKSPACE,
            base_url="https://fake.mammoth.test/api/v2",
        ),
    )


def _wire(api: Any) -> tuple[str, str, dict[str, list[str]], Any]:
    request = api.last()
    return (
        request.method,
        request.path.removeprefix("/api/v2"),
        request.query,
        request.json_body,
    )


def test_s3_pipeline_and_task_reads_have_literal_http_wires(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Cover four previously unverified task/pipeline read contracts."""

    cases = [
        (
            "view.pipeline.get",
            [str(VIEW)],
            {"dataset_id": DATASET},
            view_cmd.view_pipeline_get,
            (
                "GET",
                f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline",
                {},
                None,
            ),
        ),
        (
            "view.pipeline.items",
            [str(VIEW)],
            {
                "dataset_id": DATASET,
                "fields": "C2_S3_FIELDS",
                "limit": 23,
                "offset": 7,
                "sort": "C2_S3_SORT",
                "sequence": 19,
                "status": "C2_S3_STATUS",
            },
            view_cmd.view_pipeline_items,
            (
                "GET",
                f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/items",
                {
                    "fields": ["C2_S3_FIELDS"],
                    "limit": ["23"],
                    "offset": ["7"],
                    "sort": ["C2_S3_SORT"],
                    "sequence": ["19"],
                    "status": ["C2_S3_STATUS"],
                },
                None,
            ),
        ),
        (
            "view.task.get",
            [str(VIEW), "41"],
            {"dataset_id": DATASET},
            view_cmd.view_task_get,
            (
                "GET",
                f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks/41",
                {},
                None,
            ),
        ),
        (
            "view.task.list",
            [str(VIEW)],
            {"dataset_id": DATASET},
            view_cmd.view_task_list,
            (
                "GET",
                f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks",
                {},
                None,
            ),
        ),
    ]
    for command_id, args, body, handler, expected in cases:
        service, api = real_service(project_id=PROJECT)
        with _bound_service(monkeypatch, service):
            handler(_invocation(command_id, args, _input(tmp_path, body)))
        assert _wire(api) == expected


def test_s3_view_data_reads_have_literal_query_and_body_wires(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Cover data query, data GET, view listing, and parameter-context reads."""

    cases = [
        (
            "view.data.query",
            [str(VIEW)],
            {
                "dataset_id": DATASET,
                "sequence": 9,
                "offset": 11,
                "limit": 17,
                "columns": ["C2_S3_COLUMN"],
                "condition": {"column": "C2_S3_KEY", "operator": "EQ", "value": "C2_S3_VALUE"},
                "sort": "C2_S3_SORT",
            },
            view_cmd.view_data_query,
            (
                "POST",
                f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/data",
                {},
                {
                    "sequence": 9,
                    "offset": 11,
                    "limit": 17,
                    "columns": ["C2_S3_COLUMN"],
                    # Compiled to the backend clause shape; with no metadata
                    # on this fake the display name is sent as given.
                    "condition": {"C2_S3_KEY": {"EQ": {"VALUE": "C2_S3_VALUE"}}},
                    "sort": "C2_S3_SORT",
                },
            ),
        ),
        (
            "view.parameter-context",
            [str(VIEW)],
            {"dataset_id": DATASET},
            view_cmd.view_parameter_context,
            (
                "GET",
                f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/parameter-context",
                {},
                None,
            ),
        ),
        (
            "view.list",
            [str(DATASET)],
            {"limit": 13, "sort": "C2_S3_VIEW_SORT"},
            view_cmd.view_list,
            (
                "GET",
                f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews",
                {"limit": ["13"], "sort": ["C2_S3_VIEW_SORT"]},
                None,
            ),
        ),
    ]
    for command_id, args, body, handler, expected in cases:
        service, api = real_service(project_id=PROJECT)
        with _bound_service(monkeypatch, service):
            handler(_invocation(command_id, args, _input(tmp_path, body)))
        assert _wire(api) == expected

    # data.get has a deliberate SDK prerequisite: absent an explicit sequence,
    # it reads the latest task sequence before issuing the data GET. Assert the
    # final data request and the prerequisite path independently.
    service, api = real_service(project_id=PROJECT)
    with _bound_service(monkeypatch, service):
        view_cmd.view_data_get(
            _invocation(
                "view.data.get",
                [str(VIEW)],
                _input(tmp_path, {"dataset_id": DATASET, "timeout": 31, "poll_interval": 3}),
            )
        )
    assert [r.path.removeprefix("/api/v2") for r in api.requests] == [
        f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/items",
        f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/data",
    ]
    assert api.requests[-1].query == {"sequence": ["0"]}


def test_s3_dropped_field_is_rejected_before_transport(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A misrouted field must not disappear silently or reach the backend."""

    service, api = real_service(project_id=PROJECT)
    with _bound_service(monkeypatch, service):
        with pytest.raises(CliError, match="Unknown input field"):
            view_cmd.view_pipeline_items(
                _invocation(
                    "view.pipeline.items",
                    [str(VIEW)],
                    _input(
                        tmp_path, {"dataset_id": DATASET, "__s3_dropped_field__": "C2_SENTINEL"}
                    ),
                )
            )
    assert api.requests == []


@pytest.mark.parametrize(
    ("argv", "expected_path", "expected_query"),
    [
        (
            ["view", "pipeline", "get", str(VIEW)],
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline",
            {},
        ),
        (
            ["view", "pipeline", "items", str(VIEW)],
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/items",
            {"fields": "CLI_S3_FIELDS", "limit": "23", "offset": "7", "sequence": "19"},
        ),
        (
            ["view", "task", "get", str(VIEW), "41"],
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks/41",
            {},
        ),
        (
            ["view", "task", "list", str(VIEW)],
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks",
            {},
        ),
    ],
)
def test_true_cli_runner_reaches_recording_transport(
    argv: list[str],
    expected_path: str,
    expected_query: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    real_service: Any,
    tmp_path: Path,
) -> None:
    """Exercise Typer parsing, command dispatch, SDK, and recording HTTP."""

    service, api = real_service(project_id=PROJECT)
    _bind_runner_auth(monkeypatch)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    body: dict[str, Any] = {"dataset_id": DATASET}
    if expected_query:
        body.update({"fields": "CLI_S3_FIELDS", "limit": 23, "offset": 7, "sequence": 19})
    doc = tmp_path / "cli-s3.json"
    doc.write_text(json.dumps(body), encoding="utf-8")
    result = make_runner().invoke(
        [
            *argv,
            "--input",
            str(doc),
            "--input-format",
            "json",
            "--output",
            "json",
            "--no-input",
            "--project",
            str(PROJECT),
        ]
    )
    assert result.exit_code == 0, result.output
    request = api.last()
    assert request.path.removeprefix("/api/v2") == expected_path
    actual_query = {key: values[-1] for key, values in request.query.items()}
    assert actual_query == expected_query


def test_true_cli_wire_oracle_detects_mutated_valid_field(
    monkeypatch: pytest.MonkeyPatch, real_service: Any, tmp_path: Path
) -> None:
    """A binding regression that changes an admitted field fails the oracle."""

    service, api = real_service(project_id=PROJECT)
    _bind_runner_auth(monkeypatch)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    original_call = service.call

    def mutated_call(sdk_symbol: str, /, **kwargs: Any) -> Any:
        if sdk_symbol.endswith("PipelineAPI.items"):
            kwargs["limit"] = 999
        return original_call(sdk_symbol, **kwargs)

    monkeypatch.setattr(service, "call", mutated_call)
    doc = tmp_path / "cli-s3-mutation.json"
    doc.write_text(
        json.dumps({"dataset_id": DATASET, "fields": "CLI_S3_FIELDS", "limit": 23}),
        encoding="utf-8",
    )
    result = make_runner().invoke(
        [
            "view",
            "pipeline",
            "items",
            str(VIEW),
            "--input",
            str(doc),
            "--input-format",
            "json",
            "--output",
            "json",
            "--no-input",
            "--project",
            str(PROJECT),
        ]
    )
    assert result.exit_code == 0, result.output
    expected = {"fields": ["CLI_S3_FIELDS"], "limit": ["23"]}
    assert api.last().query["limit"] == ["999"]
    assert api.last().query != expected


@pytest.mark.parametrize(
    ("argv", "body", "expected_path", "expected_query"),
    [
        (
            ["view", "list", str(DATASET)],
            {"limit": 29, "sort": "CLI_S3_VIEW_SORT"},
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews",
            {"limit": "29", "sort": "CLI_S3_VIEW_SORT"},
        ),
        (
            ["view", "parameter-context", str(VIEW), str(DATASET)],
            {},
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/parameter-context",
            {},
        ),
        (
            ["view", "conditional-format", "list", str(VIEW), str(DATASET)],
            {},
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/conditional-format",
            {},
        ),
        (
            ["view", "data-check", "list", str(VIEW), str(DATASET)],
            {
                "fields": "CLI_S3_CHECK_FIELDS",
                "sort": "CLI_S3_CHECK_SORT",
                "sequence": "17",
                "status": "CLI_S3_CHECK_STATUS",
            },
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/data-checks",
            {
                "fields": "CLI_S3_CHECK_FIELDS",
                "sort": "CLI_S3_CHECK_SORT",
                "sequence": "17",
                "status": "CLI_S3_CHECK_STATUS",
            },
        ),
        (
            ["view", "derivative", "list", str(VIEW), str(DATASET)],
            {},
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/derivatives",
            {},
        ),
        (
            ["view", "active-user", "list", str(VIEW), str(DATASET)],
            {},
            f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/activities",
            {},
        ),
    ],
)
def test_true_cli_s3_read_runner_routes(
    argv: list[str],
    body: dict[str, Any],
    expected_path: str,
    expected_query: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    real_service: Any,
    tmp_path: Path,
) -> None:
    """Exercise six S3-owned reads through the complete CLI stack."""

    service, api = real_service(project_id=PROJECT)
    _bind_runner_auth(monkeypatch)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    doc = tmp_path / "s3-owned-read.json"
    doc.write_text(json.dumps(body), encoding="utf-8")
    result = make_runner().invoke(
        [
            *argv,
            "--input",
            str(doc),
            "--input-format",
            "json",
            "--output",
            "json",
            "--no-input",
            "--project",
            str(PROJECT),
        ]
    )
    assert result.exit_code == 0, result.output
    request = api.last()
    assert request.path.removeprefix("/api/v2") == expected_path
    assert {key: values[-1] for key, values in request.query.items()} == expected_query


def test_true_cli_s3_binding_mutation_changes_data_check_wire(
    monkeypatch: pytest.MonkeyPatch, real_service: Any, tmp_path: Path
) -> None:
    """A pre-dispatch status regression must fail the S3 literal oracle."""

    service, api = real_service(project_id=PROJECT)
    _bind_runner_auth(monkeypatch)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    original_call = service.call

    def mutated_call(sdk_symbol: str, /, **kwargs: Any) -> Any:
        if sdk_symbol.endswith("DataChecksAPI.list"):
            kwargs["status"] = "MUTATED_STATUS"
        return original_call(sdk_symbol, **kwargs)

    monkeypatch.setattr(service, "call", mutated_call)
    doc = tmp_path / "s3-check-mutation.json"
    doc.write_text(json.dumps({"status": "EXPECTED_STATUS"}), encoding="utf-8")
    result = make_runner().invoke(
        [
            "view",
            "data-check",
            "list",
            str(VIEW),
            str(DATASET),
            "--input",
            str(doc),
            "--input-format",
            "json",
            "--output",
            "json",
            "--no-input",
            "--project",
            str(PROJECT),
        ]
    )
    assert result.exit_code == 0, result.output
    expected = {"status": ["EXPECTED_STATUS"]}
    assert api.last().query["status"] == ["MUTATED_STATUS"]
    assert api.last().query != expected


def test_true_cli_data_query_wire_and_display_name_handling(
    monkeypatch: pytest.MonkeyPatch, real_service: Any, tmp_path: Path
) -> None:
    """Check distinctive query body fields and display-name relabeling."""

    service, api = real_service(project_id=PROJECT)
    _bind_runner_auth(monkeypatch)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on(
        "POST",
        r"/dataviews/278/data$",
        body={"columns": ["column_7"], "data": [{"column_7": "CLI_VALUE"}]},
    )
    api.on(
        "GET",
        r"/dataviews/278$",
        body={
            "metadata": [
                {"internal_name": "column_7", "display_name": "CLI_DISPLAY", "type": "NUMERIC"},
                {"internal_name": "column_9", "display_name": "CLI_KEY", "type": "TEXT"},
            ]
        },
    )
    doc = tmp_path / "s3-query.json"
    doc.write_text(
        json.dumps(
            {
                "sequence": 13,
                "offset": 5,
                "limit": 19,
                "columns": ["CLI_DISPLAY"],
                "condition": {"column": "CLI_KEY", "operator": "EQ", "value": "CLI_MATCH"},
                "sort": "CLI_SORT",
            }
        ),
        encoding="utf-8",
    )
    result = make_runner().invoke(
        [
            "view",
            "data",
            "query",
            str(VIEW),
            str(DATASET),
            "--input",
            str(doc),
            "--input-format",
            "json",
            "--output",
            "json",
            "--no-input",
            "--project",
            str(PROJECT),
        ]
    )
    assert result.exit_code == 0, result.output
    # One metadata read (display -> internal names and types), then the POST
    # with the condition compiled to the backend clause shape.  A TEXT
    # equality is sent as a single-item IN_LIST (the SDK's workaround for the
    # backend's TEXT + EQ type-mismatch rejection).
    wires = [(r.method, r.path.removeprefix("/api/v2").rsplit("/", 1)[-1]) for r in api.requests]
    assert wires[-2:] == [("GET", "278"), ("POST", "data")]
    assert api.requests[-1].json_body == {
        "sequence": 13,
        "offset": 5,
        "limit": 19,
        "columns": ["column_7"],
        "condition": {"column_9": {"IN_LIST": {"VALUE": ["CLI_MATCH"]}}},
        "sort": "CLI_SORT",
    }
    assert json.loads(result.output)["data"]["data"] == [{"CLI_DISPLAY": "CLI_VALUE"}]


def test_true_cli_preview_wire_and_display_name_handling(
    monkeypatch: pytest.MonkeyPatch, real_service: Any, tmp_path: Path
) -> None:
    """Check preview fields and the metadata-driven display-name path."""

    service, api = real_service(project_id=PROJECT)
    _bind_runner_auth(monkeypatch)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    api.on(
        "GET",
        r"/dataviews/278$",
        body={"metadata": [{"internal_name": "column_8", "display_name": "CLI_PREVIEW_DISPLAY"}]},
    )
    api.on(
        "GET",
        r"/dataviews/278/preview$",
        body={"columns": ["column_8"], "data": [{"column_8": "CLI_PREVIEW_VALUE"}]},
    )
    doc = tmp_path / "s3-preview.json"
    doc.write_text(json.dumps({"rows": 27, "cols": 3}), encoding="utf-8")
    result = make_runner().invoke(
        [
            "view",
            "preview",
            str(VIEW),
            str(DATASET),
            "--input",
            str(doc),
            "--input-format",
            "json",
            "--output",
            "json",
            "--no-input",
            "--project",
            str(PROJECT),
        ]
    )
    assert result.exit_code == 0, result.output
    assert api.requests[-1].query == {"rows": ["27"], "cols": ["3"]}
    assert json.loads(result.output)["data"]["columns"] == ["CLI_PREVIEW_DISPLAY"]
