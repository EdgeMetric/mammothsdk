"""Unit tests for the ``dashboard`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_ACTION = "mammoth.api.dashboards.DashboardsAPI.action"
_ANALYTICS = "mammoth.api.dashboards.DashboardsAPI.get_analytics"
_CANCEL_GENERATION = "mammoth.api.dashboards.DashboardsAPI.cancel_generation"
_CREATE = "mammoth.api.dashboards.DashboardsAPI.create"
_DATA_DRAFT = "mammoth.api.dashboards.DashboardsAPI.get_draft_data"
_DATA_PUBLISHED = "mammoth.api.dashboards.DashboardsAPI.get_publish_data"
_DELETE = "mammoth.api.dashboards.DashboardsAPI.delete"
_GET = "mammoth.api.dashboards.DashboardsAPI.get"
_GET_BY_URL = "mammoth.api.dashboards.DashboardsAPI.get_by_url"
_JOB_BY_URL = "mammoth.api.dashboards.DashboardsAPI.job_by_url"
_LIST = "mammoth.api.dashboards.DashboardsAPI.list"
_PUBLISHED_DATA_BY_URL = "mammoth.api.dashboards.DashboardsAPI.published_data_by_url"
_RESTORE = "mammoth.api.dashboards.DashboardsAPI.restore"
_SHARE = "mammoth.api.dashboards.DashboardsAPI.share"
_SOURCE_LIST = "mammoth.api.dashboards.DashboardsAPI.get_sources"
_TRASH = "mammoth.api.dashboards.DashboardsAPI.trash"
_UPDATE = "mammoth.api.dashboards.DashboardsAPI.update"
_WIDGET_DATA = "mammoth.api.dashboards.DashboardsAPI.widget_data"
_WIDGET_DATA_BY_URL = "mammoth.api.dashboards.DashboardsAPI.widget_data_by_url"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write_doc(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# --- dashboard list / get -------------------------------------------------


def test_list_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_list(_inv("dashboard.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_get_uses_positional_dashboard_id(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_get(_inv("dashboard.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"dashboard_id": 7})]


def test_get_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_get(_inv("dashboard.get"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_get_invalid_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_get(_inv("dashboard.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"


def test_get_returns_programmed_response(fake_service: FakeMammothService) -> None:
    fake_service.responses[_GET] = {"id": 7, "name": "Sales"}
    data, meta = dashboard_cmd.dashboard_get(_inv("dashboard.get", extra_args=["7"]))
    assert data == {"id": 7, "name": "Sales"}
    assert meta == {"profile": None, "workspace_id": 4, "project_id": None}


# --- dashboard get-by-url --------------------------------------------------


def test_get_by_url_uses_positional_url(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_get_by_url(_inv("dashboard.get-by-url", extra_args=["abc-slug"]))
    assert fake_service.call_log == [(_GET_BY_URL, {"url": "abc-slug"})]


def test_get_by_url_without_url_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_get_by_url(_inv("dashboard.get-by-url"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


# --- dashboard analytics ---------------------------------------------------


def test_analytics_uses_positional_dashboard_id(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_analytics(_inv("dashboard.analytics", extra_args=["9"]))
    assert fake_service.call_log == [(_ANALYTICS, {"dashboard_id": 9})]


def test_analytics_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_analytics(_inv("dashboard.analytics"))
    assert excinfo.value.code == "missing_argument"


# --- dashboard data draft / published ---------------------------------------


def test_data_draft_requires_sql(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_data_draft(_inv("dashboard.data.draft", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_data_draft_forwards_dashboard_id_and_sql(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"sql": "select 1"})
    dashboard_cmd.dashboard_data_draft(
        _inv("dashboard.data.draft", extra_args=["7"], input_file=doc)
    )
    assert fake_service.call_log == [(_DATA_DRAFT, {"dashboard_id": 7, "sql": "select 1"})]


def test_data_published_requires_sql(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_data_published(_inv("dashboard.data.published", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_data_published_forwards_dashboard_id_and_sql(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"sql": "select 2"})
    dashboard_cmd.dashboard_data_published(
        _inv("dashboard.data.published", extra_args=["7"], input_file=doc)
    )
    assert fake_service.call_log == [(_DATA_PUBLISHED, {"dashboard_id": 7, "sql": "select 2"})]


# --- dashboard job-by-url ---------------------------------------------------


def test_job_by_url_requires_job_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_job_by_url(_inv("dashboard.job-by-url", extra_args=["slug"]))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_job_by_url_without_url_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_job_by_url(_inv("dashboard.job-by-url"))
    assert excinfo.value.code == "missing_argument"


def test_job_by_url_forwards_url_and_job_id(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_job_by_url(_inv("dashboard.job-by-url", extra_args=["slug", "55"]))
    assert fake_service.call_log == [(_JOB_BY_URL, {"url": "slug", "job_id": 55})]


# --- dashboard published-data-by-url ---------------------------------------


def test_published_data_by_url_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_published_data_by_url(
            _inv("dashboard.published-data-by-url", extra_args=["slug"])
        )
    assert excinfo.value.code == "missing_field"


def test_published_data_by_url_forwards_url_and_body(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    body = {"params": {"widget_id": "00000000-0000-4000-8000-000000000001"}}
    doc = _write_doc(tmp_path, {"body": body})
    dashboard_cmd.dashboard_published_data_by_url(
        _inv("dashboard.published-data-by-url", extra_args=["slug"], input_file=doc)
    )
    assert fake_service.call_log == [(_PUBLISHED_DATA_BY_URL, {"url": "slug", "body": body})]


# --- dashboard widget-data / widget-data-by-url -----------------------------


def test_widget_data_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_widget_data(_inv("dashboard.widget-data", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_widget_data_forwards_dashboard_id_and_body(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    body = {"params": {"widgets": [{"widget_id": "00000000-0000-4000-8000-000000000001"}]}}
    doc = _write_doc(tmp_path, {"body": body})
    dashboard_cmd.dashboard_widget_data(
        _inv("dashboard.widget-data", extra_args=["7"], input_file=doc)
    )
    assert fake_service.call_log == [(_WIDGET_DATA, {"dashboard_id": 7, "body": body})]


def test_widget_data_by_url_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_widget_data_by_url(
            _inv("dashboard.widget-data-by-url", extra_args=["slug"])
        )
    assert excinfo.value.code == "missing_field"


def test_widget_data_by_url_forwards_url_and_body(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    body = {"params": {"widgets": [{"widget_id": "00000000-0000-4000-8000-000000000002"}]}}
    doc = _write_doc(tmp_path, {"body": body})
    dashboard_cmd.dashboard_widget_data_by_url(
        _inv("dashboard.widget-data-by-url", extra_args=["slug"], input_file=doc)
    )
    assert fake_service.call_log == [(_WIDGET_DATA_BY_URL, {"url": "slug", "body": body})]


# --- dashboard source list ---------------------------------------------------


def test_source_list_passes_no_kwargs(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_source_list(_inv("dashboard.source.list"))
    assert fake_service.call_log == [(_SOURCE_LIST, {})]


# --- dashboard create --------------------------------------------------------


def test_create_uses_positional_intent(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(tmp_path, {"source": [1, 2]})
    dashboard_cmd.dashboard_create(
        _inv("dashboard.create", extra_args=["Sales overview"], input_file=doc)
    )
    assert fake_service.call_log == [(_CREATE, {"intent": "Sales overview", "source": [1, 2]})]


def test_create_without_intent_is_usage_error(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"source": [1]})
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_create(_inv("dashboard.create", input_file=doc))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_create_requires_source(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_create(_inv("dashboard.create", extra_args=["Sales"]))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_create_forwards_optional_flags(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write_doc(
        tmp_path,
        {"intent": "Sales", "source": [1], "enable_filters": False, "enable_pages": True},
    )
    dashboard_cmd.dashboard_create(_inv("dashboard.create", input_file=doc))
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "intent": "Sales",
                "source": [1],
                "enable_filters": False,
                "enable_pages": True,
            },
        )
    ]


# --- dashboard update ---------------------------------------------------------


def test_update_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_update(_inv("dashboard.update", extra_args=["7"]))
    assert excinfo.value.code == "missing_field"


def test_update_forwards_dashboard_id_and_patch(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    patch = [{"op": "replace", "path": "title", "value": "X"}]
    doc = _write_doc(tmp_path, {"patch": patch})
    dashboard_cmd.dashboard_update(_inv("dashboard.update", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [(_UPDATE, {"dashboard_id": 7, "patch": patch})]


# --- dashboard action ----------------------------------------------------------


def test_action_requires_action_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_action(_inv("dashboard.action", extra_args=["7"], yes=True))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_action_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"action": "publish-data"})
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_action(
            _inv("dashboard.action", extra_args=["7"], input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_action_proceeds_with_yes_and_forwards_optional_params(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(
        tmp_path, {"action": "publish-data", "params_enabled": True, "params_view_id": 3}
    )
    dashboard_cmd.dashboard_action(
        _inv("dashboard.action", extra_args=["7"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (
            _ACTION,
            {
                "dashboard_id": 7,
                "action": "publish-data",
                "params_enabled": True,
                "params_view_id": 3,
            },
        )
    ]


# --- dashboard share ------------------------------------------------------------


def test_share_requires_type_of_auth(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_share(_inv("dashboard.share", extra_args=["7"], yes=True))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_share_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"type_of_auth": "public"})
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_share(
            _inv("dashboard.share", extra_args=["7"], input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_share_proceeds_with_yes_and_forwards_users(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write_doc(tmp_path, {"type_of_auth": "mammoth", "users": [{"email": "a@example.com"}]})
    dashboard_cmd.dashboard_share(
        _inv("dashboard.share", extra_args=["7"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (
            _SHARE,
            {
                "dashboard_id": 7,
                "type_of_auth": "mammoth",
                "users": [{"email": "a@example.com"}],
            },
        )
    ]


# --- dashboard cancel-generation / restore / trash ------------------------------


def test_cancel_generation_uses_positional_dashboard_id(
    fake_service: FakeMammothService,
) -> None:
    dashboard_cmd.dashboard_cancel_generation(_inv("dashboard.cancel-generation", extra_args=["7"]))
    assert fake_service.call_log == [(_CANCEL_GENERATION, {"dashboard_id": 7})]


def test_restore_uses_positional_dashboard_id(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_restore(_inv("dashboard.restore", extra_args=["7"]))
    assert fake_service.call_log == [(_RESTORE, {"dashboard_id": 7})]


def test_trash_uses_positional_dashboard_id(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_trash(_inv("dashboard.trash", extra_args=["7"]))
    assert fake_service.call_log == [(_TRASH, {"dashboard_id": 7})]


# --- dashboard delete ------------------------------------------------------------


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_delete(_inv("dashboard.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    dashboard_cmd.dashboard_delete(_inv("dashboard.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"dashboard_id": 7})]


def test_delete_without_id_is_usage_error(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_delete(_inv("dashboard.delete", yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


# --- async job handling (review finding #2) --------------------------------
#
# Fifteen dashboard commands return a job *handle* the caller must wait on, but
# were labelled ``not_async`` -- so the CLI returned the raw job object and
# ignored ``--job-timeout``. They are now ``always_wait`` in the manifest and
# the handler resolves the job through ``wait_if_job`` (which honors the
# service's configured job timeout). These tests pin that the handler waits.


def test_restore_resolves_job_handle(fake_service: FakeMammothService) -> None:
    fake_service.responses[_RESTORE] = {"job_id": 55}
    fake_service.job_result = {"status": "success", "resolved": True}
    data, _ = dashboard_cmd.dashboard_restore(_inv("dashboard.restore", extra_args=["7"]))
    assert "wait_if_job" in fake_service.calls
    assert fake_service.wait_log == [{"job_id": 55}]
    assert data == {"status": "success", "resolved": True}


def test_trash_resolves_job_handle(fake_service: FakeMammothService) -> None:
    fake_service.responses[_TRASH] = {"job_id": 9}
    dashboard_cmd.dashboard_trash(_inv("dashboard.trash", extra_args=["7"]))
    assert "wait_if_job" in fake_service.calls
    assert fake_service.wait_log == [{"job_id": 9}]


def test_flipped_dashboard_commands_are_always_wait() -> None:
    """The job-handle-returning dashboard commands are declared ``always_wait``.

    A structural guard on the manifest: these commands must not silently
    regress back to ``not_async`` (which would return a raw job handle).
    """
    from mammoth_cli.manifest.loader import command_by_id

    for command_id in (
        "dashboard.canvas.restore",
        "dashboard.chat.edit",
        "dashboard.data.draft",
        "dashboard.data.published",
        "dashboard.qa.ask",
        "dashboard.restore",
        "dashboard.trash",
        "dashboard.template.apply",
        "dashboard.widget-data",
        "dashboard.style.extract-brand",
    ):
        record = command_by_id(command_id)
        assert record is not None, command_id
        assert record["wait_policy"] == "always_wait", command_id
