"""`dataset find` does not list every project when the hits name theirs (mammothsdk#436)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.commands.dataset import find as find_cmd
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_SEARCH = "mammoth.api.browse.BrowseAPI.resources_search"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _named_hit(project_id: int, object_id: int, name: str) -> dict[str, object]:
    return {
        "project_id": project_id,
        "project_name": f"P{project_id}",
        "object_id": object_id,
        "name": name,
    }


def test_hits_that_name_their_project_skip_the_project_listing(
    fake_service: FakeMammothService,
) -> None:
    fake_service.projects = [{"id": 1, "name": "WRONG"}]  # would be used if it were listed
    fake_service.responses[_SEARCH] = {
        "resources": [_named_hit(1, 10, "Departments"), _named_hit(2, 11, "Departments 2")],
        "has_more": False,
    }
    result, _meta = find_cmd.dataset_find(
        Invocation(command_id="dataset.find", extra_args=["departments"])
    )
    assert "list_all_projects" not in fake_service.calls
    assert "list_projects" not in fake_service.calls
    assert [symbol for symbol, _ in fake_service.call_log] == [_SEARCH]
    assert [(m["project_id"], m["project_name"], m["id"]) for m in result["matches"]] == [
        (1, "P1", 10),
        (2, "P2", 11),
    ]


def test_scoped_find_with_named_hits_skips_the_listing_and_marks_its_own(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_SEARCH] = {
        "resources": [_named_hit(1, 9, "Sales 2023"), _named_hit(42, 10, "Sales Q1")],
        "has_more": False,
    }
    result, _meta = find_cmd.dataset_find(
        Invocation(command_id="dataset.find", project=42, extra_args=["sales"])
    )
    assert "list_all_projects" not in fake_service.calls
    assert [(m["project_id"], m["in_project"]) for m in result["matches"]] == [
        (42, True),
        (1, False),
    ]


def test_hits_without_project_names_still_list_the_projects(
    fake_service: FakeMammothService,
) -> None:
    fake_service.projects = [{"id": 1, "name": "P1"}]
    fake_service.responses[_SEARCH] = {
        "resources": [{"project_id": 1, "object_id": 10, "name": "Sales"}],
        "has_more": False,
    }
    result, _meta = find_cmd.dataset_find(
        Invocation(command_id="dataset.find", extra_args=["sales"])
    )
    assert fake_service.calls.count("list_all_projects") == 1
    assert result["projects_searched"] == 1
    assert result["matches"][0]["project_name"] == "P1"
