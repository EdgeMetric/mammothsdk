"""DashboardsAPI: request validation, wire requests and malformed-response handling.

Routes and bodies come from the pinned spec (RenameDashboardTag, SetDashboardTags,
MergeDashboardTags, CreateBlankDashboard, AddPages, ExtractContext, ExtractExemplar,
SwapDashboardData, UseTemplate, DashboardV3TakePendingTemplate, RenderFigureSvg, AssessTwb,
AssessPbix, ImportWorkbookDataset, CreateAttachment, PowerbiPreflight, TableauPreflightHandler).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema, spec

Call = Callable[[Any], Awaitable[Any]]


def _only(server: RecordingServer) -> dict[str, Any]:
    assert len(server.requests) == 1
    return server.requests[0]


# --- list / tags ----------------------------------------------------------------------------------


async def test_list_with_a_project_filters_by_project_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /dashboards"] = {"dashboards": [{"id": 1}]}
    assert await client.dashboards.list(project_id=7) == [{"id": 1}]
    assert _only(server)["query"] == {"project_id": "7"}


FULL_PREFLIGHT = {
    "exportable": True,
    "blocked_reason": None,
    "figures_total": 5,
    "figures_exported": 4,
    "figures_refused": 1,
    "degraded": False,
    "refusals": [],
    "row_count": 10,
    "column_count": 3,
}


async def test_tag_calls_hit_the_spec_routes_with_spec_bodies(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.dashboards.list_tags()
    await client.dashboards.rename_tag(4, "Finance")
    await client.dashboards.set_tags(9, ["a", "b"])
    await client.dashboards.merge_tag(4, 5)
    await client.dashboards.delete_tag(4)
    assert [(r["method"], r["path"], r["body"]) for r in server.requests] == [
        ("GET", "/dashboards/tags", None),
        ("PATCH", "/dashboards/tags/4", {"name": "Finance"}),
        ("PUT", "/dashboards/9/tags", {"tags": ["a", "b"]}),
        ("POST", "/dashboards/tags/4/merge", {"target_id": 5}),
        ("DELETE", "/dashboards/tags/4", None),
    ]
    paths = spec()["paths"]
    for method, template in (
        ("get", "/dashboards/tags"),
        ("patch", "/dashboards/tags/{tag_id}"),
        ("put", "/dashboards/{dashboard_id}/tags"),
        ("post", "/dashboards/tags/{tag_id}/merge"),
        ("delete", "/dashboards/tags/{tag_id}"),
    ):
        assert method in paths[template]
    assert schema("TagMergeParams")["required"] == ["target_id"]


TAG_REFUSALS: list[tuple[Call, str]] = [
    (lambda a: a.rename_tag(0, "x"), "`tag_id` must be a positive integer, got 0"),
    (lambda a: a.rename_tag(True, "x"), "`tag_id` must be a positive integer, got True"),
    (lambda a: a.rename_tag(1, 5), "Invalid tag rename parameters"),
    (lambda a: a.rename_tag(1, "   "), "`name` must be non-blank"),
    (lambda a: a.set_tags(0, []), "`dashboard_id` must be a positive integer, got 0"),
    (lambda a: a.set_tags(1, "tag"), "`tags` must be a list of strings"),
    (lambda a: a.set_tags(1, ["ok", 3]), "`tags` must be a list of strings"),
    (lambda a: a.delete_tag(-1), "`tag_id` must be a positive integer, got -1"),
    (lambda a: a.merge_tag(0, 2), "`tag_id` must be a positive integer, got 0"),
    (lambda a: a.merge_tag(1, 0), "`target_id` must be a positive integer, got 0"),
    (lambda a: a.merge_tag(3, 3), "`tag_id` and `target_id` must differ"),
]


@pytest.mark.parametrize(("call", "message"), TAG_REFUSALS)
async def test_tag_calls_refuse_bad_input_before_any_request(
    call: Call, message: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await call(client.dashboards)
    assert server.requests == []


# --- request models are validated before sending ----------------

BAD_REQUESTS: list[tuple[Call, str]] = [
    (lambda a: a.create_blank({"dataview_id": "abc"}), "Invalid blank dashboard parameters"),
    (lambda a: a.create_blank({"dataview_id": 0}), "`dataview_id` must be a positive integer"),
    (lambda a: a.generate_v3({"nope": 1}), "Invalid dashboard generation parameters"),
    (lambda a: a.add_pages(0, {"params": {"pages": []}}), "`dashboard_id` must be a positive"),
    (lambda a: a.add_pages(1, {"params": "x"}), "Invalid add-pages parameters"),
    (lambda a: a.extract_context({"params": "x"}), "Invalid context-extract parameters"),
    (lambda a: a.extract_exemplar({"params": "x"}), "Invalid exemplar-extract parameters"),
    (lambda a: a.swap_data(0, {"params": {"dataview_id": 1}}), "`dashboard_id` must be a positive"),
    (lambda a: a.swap_data(1, {"params": "x"}), "Invalid swap-data parameters"),
    (lambda a: a.use_template("", {"params": {"project_id": 1}}), "`slug` must be a non-empty"),
    (lambda a: a.use_template("s", {"params": "x"}), "Invalid use-template parameters"),
    (lambda a: a.render_figure_svg({}), "`spec` must be a non-empty dict"),
    (lambda a: a.powerbi_preflight(0), "`dashboard_id` must be a positive"),
    (lambda a: a.tableau_preflight(True), "`dashboard_id` must be a positive"),
    (lambda a: a.powerbi_export_artifact(0), "`dashboard_id` must be a positive"),
    (lambda a: a.tableau_export_artifact(-1), "`dashboard_id` must be a positive"),
]


@pytest.mark.parametrize(("call", "message"), BAD_REQUESTS)
async def test_invalid_requests_are_refused_before_any_request(
    call: Call, message: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await call(client.dashboards)
    assert server.requests == []


# --- good requests: wire shape ----------------


async def test_add_pages_wraps_the_spec_params_and_parses_the_answer(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /dashboards/3/pages"] = {"bake_job_id": 5, "sequence": 2}
    reply = await client.dashboards.add_pages(3, {"params": {"pages": [{"title": "p"}]}})  # type: ignore[arg-type]
    assert _only(server)["body"] == {"params": {"pages": [{"title": "p"}]}}
    assert reply.bake_job_id == 5 and reply.sequence == 2
    assert set(schema("AddPagesResponse")["required"]) == {"bake_job_id", "sequence"}


async def test_swap_data_posts_to_the_v3_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/3/swap-data"] = (201, {"job_id": 8})
    reply = await client.dashboards.swap_data(3, {"params": {"dataview_id": 11}})  # type: ignore[arg-type]
    assert _only(server)["body"] == {"params": {"dataview_id": 11}}
    assert reply.job_id == 8


async def test_use_template_percent_encodes_the_slug_and_returns_a_job_response(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    job = {
        "id": 4,
        "status": "processing",
        "response": {},
        "operation": "x",
        "path": "/x",
        "created_at": "2026-09-01T10:00:00",
        "last_updated_at": "2026-09-01T10:00:00",
    }
    server.answers["POST /dashboards/v3/templates/a%20b%2Fc/use"] = (202, {"job": job})
    reply = await client.dashboards.use_template("a b/c", {"params": {"project_id": 2}})  # type: ignore[arg-type]
    assert _only(server)["body"] == {"params": {"project_id": 2, "style_id": ""}}  # spec default
    assert reply.job.id == 4  # type: ignore[union-attr]


async def test_use_template_returns_an_object_job_for_the_plain_answer(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/templates/t/use"] = (201, {"job_id": 6})
    reply = await client.dashboards.use_template("t", {"params": {"project_id": 2}})  # type: ignore[arg-type]
    assert reply.job_id == 6  # type: ignore[union-attr]


async def test_render_figure_svg_returns_the_svg_text(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/render/svg"] = {"svg": "<svg/>"}
    assert await client.dashboards.render_figure_svg({"mark": "bar"}, style_id="s1") == "<svg/>"
    assert _only(server)["body"] == {"spec": {"mark": "bar"}, "style_id": "s1"}
    assert set(schema("RenderFigureSvgSpec")["properties"]) == {"spec", "style_id"}


@pytest.mark.parametrize("answer", [{}, {"svg": ""}, {"svg": 3}])
async def test_render_figure_svg_rejects_an_answer_without_svg_text(
    answer: dict[str, Any], server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/render/svg"] = answer
    with pytest.raises(MammothValidationError, match="no `svg` string"):
        await client.dashboards.render_figure_svg({"mark": "bar"})


async def test_pending_template_returns_the_slug(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/templates/pending"] = {"slug": "sales"}
    assert (await client.dashboards.take_pending_template())["slug"] == "sales"


# --- answers that do not match the model are reported, not passed on ----------------

BAD_ANSWERS: list[tuple[Call, str, str, Any, str]] = [
    (
        lambda a: a.add_pages(3, {"params": {"pages": [{"title": "p"}]}}),
        "POST /dashboards/3/pages",
        "Invalid add-pages response",
        {"sequence": "x"},
        "",
    ),
    (
        lambda a: a.extract_context({"params": {"name": "n"}}),
        "POST /dashboards/v3/contexts/extract",
        "Invalid context-extract response",
        {"figureHeavy": "not-a-list"},
        "",
    ),
    (
        lambda a: a.extract_exemplar({"params": {"name": "n"}}),
        "POST /dashboards/v3/exemplar/extract",
        "Invalid exemplar-extract response",
        {"palette": "not-a-list"},
        "",
    ),
    (
        lambda a: a.swap_data(3, {"params": {"dataview_id": 1}}),
        "POST /dashboards/v3/3/swap-data",
        "Invalid swap-data response",
        {"job_id": "abc"},
        "",
    ),
    (
        lambda a: a.take_pending_template(),
        "POST /dashboards/v3/templates/pending",
        "Invalid pending-template response",
        {"slug": ["x"]},
        "",
    ),
    (
        lambda a: a.use_template("t", {"params": {"project_id": 1}}),
        "POST /dashboards/v3/templates/t/use",
        "Invalid use-template response",
        {"job_id": "abc"},
        "",
    ),
    (
        lambda a: a.powerbi_preflight(3),
        "GET /dashboards/3/powerbi",
        "Invalid Power BI preflight response",
        {"exportable": "maybe"},
        "",
    ),
    (
        lambda a: a.tableau_preflight(3),
        "GET /dashboards/3/tableau",
        "Invalid Tableau preflight response",
        {"exportable": "maybe"},
        "",
    ),
]


@pytest.mark.parametrize(("call", "route", "message", "answer", "_"), BAD_ANSWERS)
async def test_a_malformed_answer_raises_a_validation_error_naming_the_call(
    call: Call,
    route: str,
    message: str,
    answer: Any,
    _: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    server.answers[route] = answer
    with pytest.raises(MammothValidationError, match=message):
        await call(client.dashboards)
    assert len(server.requests) == 1


async def test_context_and_exemplar_extract_post_their_params_and_return_plain_dicts(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/contexts/extract"] = {"suggestions": {"a": "x"}}
    server.answers["POST /dashboards/v3/exemplar/extract"] = {"palette": ["#fff"]}
    ctx = await client.dashboards.extract_context({"params": {"name": "brief.pdf", "size": 3}})  # type: ignore[arg-type]
    exm = await client.dashboards.extract_exemplar({"params": {"name": "ex.png"}})  # type: ignore[arg-type]
    assert [r["body"] for r in server.requests] == [
        {"params": {"name": "brief.pdf", "size": 3}},
        {"params": {"name": "ex.png", "size": 0}},
    ]
    assert isinstance(ctx, dict) and ctx["suggestions"] == {"a": "x"}
    assert isinstance(exm, dict) and exm["palette"] == ["#fff"]


# --- preflight / export artifacts ----------------


@pytest.mark.parametrize("target", ["powerbi", "tableau"])
async def test_preflights_get_the_dashboard_route(
    target: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET /dashboards/3/{target}"] = FULL_PREFLIGHT
    reply = await getattr(client.dashboards, f"{target}_preflight")(3)
    assert _only(server) == {
        "method": "GET",
        "path": f"/dashboards/3/{target}",
        "query": {},
        "body": None,
    }
    assert reply.exportable is True and reply.figures_exported == 4
    assert "get" in spec()["paths"][f"/dashboards/{{dashboard_id}}/{target}"]


@pytest.mark.xfail(
    strict=True,
    reason="BUG: DashboardBiPreflightResponse requires figures_*, degraded, refusals and "
    "row/column counts, but the spec's PowerBiPreflightResponse only requires `exportable`",
)
async def test_preflight_parses_an_answer_with_only_the_spec_required_field(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    assert schema("PowerBiPreflightResponse")["required"] == ["exportable"]
    server.answers["GET /dashboards/3/powerbi"] = {"exportable": False, "blocked_reason": "x"}
    reply = await client.dashboards.powerbi_preflight(3)
    assert reply.exportable is False


# --- file uploads -------------


def _file(tmp: Path, name: str = "w.twb") -> Path:
    path = tmp / name
    path.write_text("<workbook/>")
    return path


@pytest.mark.parametrize(
    ("method", "route"),
    [
        ("assess_twb", "/dashboards/v3/twb/assess"),
        ("assess_pbix", "/dashboards/v3/pbix/assess"),
        ("attachment_create", "/dashboards/v3/attachments"),
    ],
)
async def test_workbook_uploads_send_the_file_as_a_multipart_part_named_file(
    method: str,
    route: str,
    server: RecordingServer,
    client: MammothClient,
    tmp_path: Path,  # noqa: F811
) -> None:
    server.answers[f"POST {route}"] = {"source": {"name": "w.twb"}}
    await getattr(client.dashboards, method)(_file(tmp_path))
    sent = _only(server)
    assert (sent["method"], sent["path"], sent["query"]) == ("POST", route, {})
    assert 'name="file"; filename="w.twb"' in sent["body"] and "<workbook/>" in sent["body"]


async def test_assess_uploads_parse_the_assessment(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/twb/assess"] = {"assessment": {"score": 3}}
    assessed = await client.dashboards.assess_twb(_file(tmp_path))
    assert assessed.assessment == {"score": 3}


async def test_assess_upload_reports_an_answer_it_cannot_parse(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/pbix/assess"] = {"assessment": "not-an-object"}
    with pytest.raises(MammothValidationError, match="Invalid workbook assessment response"):
        await client.dashboards.assess_pbix(_file(tmp_path, "m.pbix"))


async def test_import_workbook_sends_the_project_as_a_form_field(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/import/dataset"] = (
        201,
        {"dataview_id": 12, "dataset_name": "Sales"},
    )
    reply = await client.dashboards.import_workbook(_file(tmp_path), project_id=7)
    body = _only(server)["body"]
    assert 'name="project_id"' in body and "\r\n\r\n7\r\n" in body
    assert 'name="file"; filename="w.twb"' in body
    assert reply.dataview_id == 12 and reply.dataset_name == "Sales"
    assert set(schema("ImportWorkbookForm")["properties"]) == {"file", "project_id"}


async def test_import_workbook_without_a_project_sends_only_the_file(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    await client.dashboards.import_workbook(str(_file(tmp_path)))
    assert 'name="project_id"' not in _only(server)["body"]


async def test_import_workbook_reports_an_answer_it_cannot_parse(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/import/dataset"] = (201, {"dataview_id": "abc"})
    with pytest.raises(MammothValidationError, match="Invalid workbook import response"):
        await client.dashboards.import_workbook(_file(tmp_path))


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda a, p: a.import_workbook(p / "missing.twb"), "File not found"),
        (lambda a, p: a.import_workbook(p, project_id=1), "File not found"),
        (
            lambda a, p: a.import_workbook(_file(p), project_id="7"),
            "`project_id` must be an integer",
        ),
        (
            lambda a, p: a.import_workbook(_file(p), project_id=True),
            "`project_id` must be an integer",
        ),
        (lambda a, p: a.import_workbook(None), "`file` must be a valid local path"),
        (lambda a, p: a.assess_twb(p / "missing.twb"), "File not found"),
        (lambda a, p: a.assess_pbix(None), "`file` must be a valid local path"),
        (lambda a, p: a.attachment_create(p / "missing.pdf"), "File not found"),
    ],
)
async def test_uploads_are_refused_before_any_request(
    call: Callable[[Any, Path], Awaitable[Any]],
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
    tmp_path: Path,
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await call(client.dashboards, tmp_path)
    assert server.requests == []


@pytest.mark.skipif(
    __import__("os").geteuid() == 0, reason="root can open files regardless of mode"
)
async def test_an_unreadable_file_is_reported_as_cannot_be_opened(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    path = _file(tmp_path)
    path.chmod(0)
    try:
        with pytest.raises(MammothValidationError, match="File cannot be opened"):
            await client.dashboards.assess_twb(path)
        with pytest.raises(MammothValidationError, match="File cannot be opened"):
            await client.dashboards.import_workbook(path)
    finally:
        path.chmod(0o600)
    assert server.requests == []
