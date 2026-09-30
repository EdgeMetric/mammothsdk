"""Unit tests for the D-077 ``state`` read-back on the families this agent
owns: dashboard, data-app, snippet, annotation, template.

Unlike the generic mechanism tests (``tests/unit/runtime/test_state.py``,
fake ``command_by_id``/``HANDLERS``), these exercise the *real* manifest
declarations landed in ``spec/manifests/commands/{dashboard,data-app,snippet,
annotation,template}.yaml`` against the *real* registered command handlers,
through ``with_state`` directly -- one test per readback kind actually used
by these families (object, delivery), one showing the empty-``ids`` parent-
listing pattern used by several deletes, and one confirming ``no_readback``
adds nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import with_state
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_DASHBOARD_GET = "mammoth.api.dashboards.DashboardsAPI.get"
_JOB_GET = "mammoth.api.jobs.JobsAPI.get_job"
_ANNOTATION_LIST = "mammoth.api.annotations.AnnotationsAPI.list"
_DATA_APP_GET = "mammoth.api.data_apps.DataAppsAPI.get"
_SNIPPET_GET = "mammoth.api.snippets.SnippetsAPI.get"
_TEMPLATE_LIST = "mammoth.api.templates.TemplatesAPI.list"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(command_id: str, extra_args: list[str], project: int = 10) -> Invocation:
    return Invocation(command_id=command_id, output="json", project=project, extra_args=extra_args)


# ---------------------------------------------------------------------------
# kind: object -- a plain lifecycle write on a dashboard reads back the
# dashboard record itself.
# ---------------------------------------------------------------------------


def test_dashboard_archive_readback_is_kind_object(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DASHBOARD_GET] = {"id": 123, "name": "Sales", "archived": True}
    result = with_state(_inv("dashboard.archive", ["123"]), {"status": "done"})
    assert result["state"] == {
        "kind": "object",
        "read_by": "dashboard.get 123",
        "object": {"id": 123, "name": "Sales", "archived": True},
    }


# ---------------------------------------------------------------------------
# kind: delivery -- a write whose result carries only a job_id (no other
# resource handle) reads back the job's status via the cross-family
# ``job.get``.
# ---------------------------------------------------------------------------


def test_dashboard_v3_generate_readback_is_kind_delivery(fake_service: FakeMammothService) -> None:
    fake_service.responses[_JOB_GET] = {"status": "done", "message": "dashboard 456 created"}
    result = with_state(_inv("dashboard.v3.generate", []), {"job_id": 7660, "status_code": None})
    assert result["state"] == {
        "kind": "delivery",
        "read_by": "job.get 7660",
        "status": "done",
        "detail": "dashboard 456 created",
    }


# ---------------------------------------------------------------------------
# kind: object, empty ids -- a delete reads back the parent listing (the
# only way to show "it's gone" when the delete itself returns nothing
# addressable).
# ---------------------------------------------------------------------------


def test_annotation_delete_readback_is_parent_listing_with_empty_ids(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_ANNOTATION_LIST] = [
        {"id": 1, "target_type": "dataview", "target_id": 42}
    ]
    result = with_state(_inv("annotation.delete", ["5"]), {})
    assert result["state"] == {
        "kind": "object",
        "read_by": "annotation.list",
        "object": [{"id": 1, "target_type": "dataview", "target_id": 42}],
    }


def test_template_delete_readback_is_parent_listing_with_empty_ids(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_TEMPLATE_LIST] = {"templates": [{"id": 9, "name": "Q1 report"}]}
    result = with_state(_inv("template.delete", ["3"]), {})
    assert result["state"] == {
        "kind": "object",
        "read_by": "template.list",
        "object": [{"id": 9, "name": "Q1 report"}],
    }


# ---------------------------------------------------------------------------
# kind: object -- data-app and snippet families, each keyed off the write's
# own positional id.
# ---------------------------------------------------------------------------


def test_data_app_update_readback_is_kind_object(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DATA_APP_GET] = {"id": 55, "name": "Ops app"}
    result = with_state(_inv("data-app.update", ["55"]), {"status": "done"})
    assert result["state"] == {
        "kind": "object",
        "read_by": "data-app.get 55",
        "object": {"id": 55, "name": "Ops app"},
    }


def test_snippet_duplicate_readback_sources_id_from_result(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_SNIPPET_GET] = {"id": 202, "name": "cleaner (copy)"}
    result = with_state(_inv("snippet.duplicate", ["201"]), {"id": 202, "name": "cleaner (copy)"})
    assert result["state"] == {
        "kind": "object",
        "read_by": "snippet.get 202",
        "object": {"id": 202, "name": "cleaner (copy)"},
    }


# ---------------------------------------------------------------------------
# no_readback -- declared writes add no state block at all.
# ---------------------------------------------------------------------------


def test_dashboard_descriptor_data_declares_no_readback(fake_service: FakeMammothService) -> None:
    result = with_state(
        _inv("dashboard.descriptor-data", ["123"]),
        {"ef28f9bcc263c0f7": {"status": "ok", "value": 1}},
    )
    assert "state" not in result
