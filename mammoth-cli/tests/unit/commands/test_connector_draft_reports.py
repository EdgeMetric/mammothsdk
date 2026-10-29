"""``connector draft`` reads that report their sample honestly (issues #356 and #357)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands.dashboard.generated import generated_dashboard
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_PREVIEW = "mammoth.api.connector_drafts.ConnectorDraftsAPI.preview_source"
_SOURCES = "mammoth.api.connector_drafts.ConnectorDraftsAPI.sources"
_DRAFT = "mammoth.api.connector_drafts.ConnectorDraftsAPI.get"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _preview(tmp_path: Path, limit: int) -> Invocation:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": limit}), encoding="utf-8")
    return Invocation(
        command_id="connector.draft.source.preview",
        extra_args=["9", "s19"],
        input_file=str(doc),
        project=180,
    )


def test_a_preview_short_of_its_limit_on_a_bigger_source_says_it_was_capped(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_PREVIEW] = {"columns": ["a"], "rows": [{"a": 1}] * 10, "row_count": 10}
    fake_service.responses[_SOURCES] = {"sources": [{"id": "s19", "row_count": 76}]}

    data, _ = generated_dashboard(_preview(tmp_path, 100))

    assert data["capped"] is True
    assert data["limit_requested"] == 100
    assert data["limit_applied"] == 10
    assert data["source_row_count"] == 76
    assert fake_service.call_log[0] == (_PREVIEW, {"draft_id": 9, "source_id": "s19", "limit": 100})
    assert fake_service.call_log[1] == (_SOURCES, {"draft_id": 9})


def test_a_preview_that_returns_all_it_was_asked_for_reads_nothing_more(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_PREVIEW] = {"rows": [{"a": 1}] * 5, "row_count": 5}

    data, _ = generated_dashboard(_preview(tmp_path, 5))

    assert "capped" not in data
    assert [symbol for symbol, _ in fake_service.call_log] == [_PREVIEW]


def test_draft_read_describes_the_sample_behind_a_per_parent_table(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_DRAFT] = {
        "id": 9,
        "sources": [
            {"id": "s1", "name": "invoice_run", "row_count": 76},
            {
                "id": "s2",
                "name": "invoices",
                "each": {"source": "s1", "capped": True, "failed": 3, "read": 17, "total": 20},
            },
        ],
    }

    data, _ = generated_dashboard(
        Invocation(command_id="connector.draft.get", extra_args=["9"], project=180)
    )

    assert data["sources"][1]["each"]["summary"] == "sampled 20 of 76 parents; 17 read, 3 failed"
