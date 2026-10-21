"""``browse resources / resource / search / resources bulk``, and folder ids in browse output.

Contract (``mammoth_cli/services/folder_ids.py``): the backend keys a folder by a label id and by a
resource id; the CLI shows and accepts only the resource id, so every folder in an answer is
rewritten to its resource id and every folder id the caller gives is looked up to its label id
before the SDK is called. A dataset hit carries ``dataset_id`` and a view hit ``view_id`` beside
the tree id (``browse_search`` docstring). ``dataset`` / ``folder`` are the route's
``datasource`` / ``label``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import browse as browse_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.folder_ids import FolderIds
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.folders.FoldersAPI.list"
_RESOURCES = "mammoth.api.browse.BrowseAPI.resources_list"
_RESOURCE = "mammoth.api.browse.BrowseAPI.resource_get"
_SEARCH = "mammoth.api.browse.BrowseAPI.resources_search"
_BULK = "mammoth.api.browse.BrowseAPI.resources_bulk"
_ANCESTORS = "mammoth.api.browse.BrowseAPI.resource_ancestors"
_FOLDERS = {"folders": [{"id": 7, "resource_id": 707}, {"id": 8, "resource_id": 808}]}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _input(tmp_path: Path, document: dict[str, Any]) -> str:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return str(path)


def _calls(service: FakeMammothService, symbol: str) -> list[dict[str, Any]]:
    return [kwargs for name, kwargs in service.call_log if name == symbol]


# ── browse resources ──


def test_resources_forwards_the_paging_and_filter_fields_it_knows(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_RESOURCES] = {"resources": []}
    document = {
        "parent_type": "label",
        "parent_id": 5,
        "resource_type": "dataset",
        "search": "sales",
        "cursor": "c1",
        "limit": 10,
        "sort": "name",
        "fields": "id,name",
    }
    browse_cmd.browse_resources(
        _inv("browse.resources", project=180, input_file=_input(tmp_path, document))
    )
    assert _calls(fake_service, _RESOURCES) == [{"project_id": 180, **document}]


def test_resources_names_the_dataset_and_view_ids_beside_the_tree_id(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_RESOURCES] = {
        "resources": [
            {"id": 1, "resource_type": "datasource", "object_id": 91},
            {"id": 2, "resource_type": "dataview", "object_id": 92},
            {"id": 3, "resource_type": "report", "object_id": 93},
            "not a row",
        ],
        "next_cursor": "c2",
    }
    data, meta = browse_cmd.browse_resources(_inv("browse.resources", project=180))
    assert data["resources"] == [
        {"id": 1, "resource_type": "datasource", "object_id": 91, "dataset_id": 91},
        {"id": 2, "resource_type": "dataview", "object_id": 92, "view_id": 92},
        {"id": 3, "resource_type": "report", "object_id": 93},
        "not a row",
    ]
    assert data["next_cursor"] == "c2"
    assert meta["project_id"] == 180


def test_an_answer_with_no_resource_list_is_returned_unchanged(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_RESOURCES] = {"count": 0}
    data, _ = browse_cmd.browse_resources(_inv("browse.resources", project=180))
    assert data == {"count": 0}


def test_resources_needs_a_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_resources(_inv("browse.resources"))
    assert excinfo.value.code == "project_required"


def test_a_folder_row_in_resources_is_shown_by_its_resource_id(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_RESOURCES] = {
        "resources": [
            {
                "id": 55,
                "resource_type": "label",
                "resource_id": 707,
                "object_id": 7,
                "object_properties": {"resource_id": 707, "name": "Q1"},
            }
        ]
    }
    data, _ = browse_cmd.browse_resources(_inv("browse.resources", project=180))
    assert data["resources"] == [
        {
            "id": 707,
            "resource_type": "label",
            "object_properties": {"name": "Q1", "id": 707},
        }
    ]


# ── browse resource ──


def test_resource_needs_a_type_and_an_id(fake_service: FakeMammothService) -> None:
    for extra in ([], ["dataset"]):
        with pytest.raises(CliError) as excinfo:
            browse_cmd.browse_resource(_inv("browse.resource", project=180, extra_args=extra))
        assert excinfo.value.code == "missing_argument"
        assert excinfo.value.message == "This command requires a resource type and a resource id."
    assert fake_service.call_log == []


def test_resource_passes_the_type_alias_and_id_as_the_routes_names(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_RESOURCE] = {"id": 123}
    browse_cmd.browse_resource(_inv("browse.resource", project=180, extra_args=["dataset", "123"]))
    assert _calls(fake_service, _RESOURCE) == [
        {"resource_type": "datasource", "object_id": 123, "project_id": 180}
    ]
    assert _calls(fake_service, _LIST) == []  # only folders need the folder listing


def test_a_folder_is_asked_for_by_its_label_id_and_answered_by_its_resource_id(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    fake_service.responses[_RESOURCE] = {
        "id": 55,
        "resource_type": "label",
        "resource_id": 707,
        "object_id": 7,
    }
    data, _ = browse_cmd.browse_resource(
        _inv("browse.resource", project=180, extra_args=["folder", "707"])
    )
    assert _calls(fake_service, _RESOURCE) == [
        {"resource_type": "label", "object_id": 7, "project_id": 180}
    ]
    assert data == {"id": 707, "resource_type": "label"}


def test_a_folder_id_the_project_does_not_have_is_not_found(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_resource(
            _inv("browse.resource", project=180, extra_args=["folder", "999"])
        )
    assert excinfo.value.code == "resource_not_found"
    assert excinfo.value.exit_status == 5
    assert excinfo.value.message == "No folder with id 999 in project 180."
    assert excinfo.value.details == {"type": "folder", "id": 999, "project_id": 180}
    assert _calls(fake_service, _RESOURCE) == []


# ── browse search ──


def test_search_forwards_its_fields_and_names_the_ids_of_what_it_found(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_SEARCH] = {
        "resources": [{"id": 4, "resource_type": "datasource", "object_id": 40}]
    }
    document = {"search": "sales", "resource_type": "dataset,folder", "limit": 5}
    data, meta = browse_cmd.browse_search(
        _inv("browse.search", input_file=_input(tmp_path, document))
    )
    assert _calls(fake_service, _SEARCH) == [
        {"search": "sales", "resource_type": "datasource,label", "limit": 5}
    ]
    assert data["resources"][0]["dataset_id"] == 40
    assert meta["project_id"] is None


def test_a_search_with_no_resource_type_sends_none(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    browse_cmd.browse_search(
        _inv("browse.search", input_file=_input(tmp_path, {"search": "x", "cursor": "c"}))
    )
    assert _calls(fake_service, _SEARCH) == [{"search": "x", "cursor": "c"}]


# ── browse resources bulk ──


def test_bulk_needs_items(fake_service: FakeMammothService, tmp_path: Path) -> None:
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_resources_bulk(
            _inv("browse.resources.bulk", project=180, input_file=_input(tmp_path, {}))
        )
    assert excinfo.value.code == "missing_field"
    assert excinfo.value.message == "This command requires the 'items' input field."
    assert fake_service.call_log == []


def test_bulk_turns_folder_ids_into_label_ids_and_leaves_other_pairs_alone(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    fake_service.responses[_BULK] = [{"id": 1, "resource_type": "dataview"}]
    document = {"items": [["dataview", 42], ["label", 808], ["label", 707]]}
    data, meta = browse_cmd.browse_resources_bulk(
        _inv("browse.resources.bulk", project=180, input_file=_input(tmp_path, document))
    )
    assert _calls(fake_service, _BULK) == [
        {"items": [["dataview", 42], ["label", 8], ["label", 7]], "project_id": 180}
    ]
    assert data == {"resources": [{"id": 1, "resource_type": "dataview"}]}
    assert meta["project_id"] == 180
    assert len(_calls(fake_service, _LIST)) == 1  # one listing for all the folders


def test_bulk_with_an_unknown_folder_asks_nothing_of_the_resource_route(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_resources_bulk(
            _inv(
                "browse.resources.bulk",
                project=180,
                input_file=_input(tmp_path, {"items": [["label", 5]]}),
            )
        )
    assert excinfo.value.message == "No folder with id 5 in project 180."
    assert _calls(fake_service, _BULK) == []


# ── ancestors ──


def test_ancestors_shows_each_folder_on_the_path_by_its_resource_id(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    fake_service.responses[_ANCESTORS] = {
        "ancestors": [{"type": "label", "id": 7, "url": "/data/folders/7"}]
    }
    data, _ = browse_cmd.browse_ancestors(_inv("browse.ancestors", project=180, extra_args=["808"]))
    assert data == {"ancestors": [{"type": "label", "id": 707, "url": "/data/folders/707"}]}


def test_ancestors_error_other_than_not_found_passes_through(
    fake_service: FakeMammothService,
) -> None:
    boom = CliError(code="api_error", message="server said no", exit_status=1)
    fake_service.responses[_ANCESTORS] = boom
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_ancestors(_inv("browse.ancestors", project=180, extra_args=["808"]))
    assert excinfo.value is boom


def test_ancestors_of_a_non_folder_is_the_needs_a_folder_error(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_ANCESTORS] = CliError(
        code="resource_not_found", message="404", exit_status=5
    )
    with pytest.raises(CliError) as excinfo:
        browse_cmd.browse_ancestors(_inv("browse.ancestors", project=180, extra_args=["812"]))
    assert excinfo.value.message == "browse ancestors needs a FOLDER id; this id is not a folder."
    assert excinfo.value.exit_status == 5


# ── FolderIds ──


def test_the_folder_listing_is_read_a_page_of_a_hundred_at_a_time_until_a_short_page(
    fake_service: FakeMammothService,
) -> None:
    first = {"folders": [{"id": n, "resource_id": 1000 + n} for n in range(100)]}
    second = {"folders": [{"id": 100, "resource_id": 1100}]}
    pages = iter([first, second])
    fake_service.responses[_LIST] = lambda log: next(pages)
    mapping = FolderIds(fake_service).to_open(180)
    assert len(mapping) == 101
    assert mapping[100] == 1100
    assert [kw["offset"] for kw in _calls(fake_service, _LIST)] == [0, 100]
    assert {kw["limit"] for kw in _calls(fake_service, _LIST)} == {100}


def test_a_folder_without_both_ids_is_left_out_of_the_map(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = {
        "folders": [{"id": 1}, {"resource_id": 2}, {"id": 3, "resource_id": 33}, "x"]
    }
    assert FolderIds(fake_service).to_open(180) == {3: 33}


def test_a_folder_record_shows_its_resource_id_parent_and_path_by_resource_ids(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    record = {
        "id": 8,
        "resource_id": 808,
        "parent_id": "label_7",
        "resource_path": "project:180/label:Q1:7/label:Q2:8",
        "name": "Q2",
    }
    opened = FolderIds(fake_service).open_folder(180, record)
    assert opened == {
        "id": 808,
        "parent_id": 707,
        "resource_path": "project:180/label:Q1:707/label:Q2:808",
        "name": "Q2",
    }


def test_the_project_root_folder_has_no_resource_id_and_is_returned_as_is(
    fake_service: FakeMammothService,
) -> None:
    root = {"id": 1, "name": "root"}
    assert FolderIds(fake_service).open_folder(180, root) == root
    assert _calls(fake_service, _LIST) == []


def test_a_parent_that_is_not_a_known_label_keeps_its_value(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    opened = FolderIds(fake_service).open_folder(
        180, {"id": 8, "resource_id": 808, "parent_id": "label_99"}
    )
    assert opened["parent_id"] == "label_99"


def test_a_browse_tree_names_its_project_and_opens_the_folders_beneath_it(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    tree = {
        "type": "project",
        "id": 180,
        "children": [
            {"type": "label", "id": 7, "url": "/p/180/folders/7"},
            {"type": "label", "id": 4040, "url": "/p/180/folders/4040"},
            {"type": "datasource", "id": 7},
        ],
    }
    data = FolderIds(fake_service).open_data(tree, None)
    assert data["children"] == [
        {"type": "label", "id": 707, "url": "/p/180/folders/707"},
        {"type": "label", "id": 4040, "url": "/p/180/folders/4040"},  # not a folder of the project
        {"type": "datasource", "id": 7},  # only labels are folders
    ]


def test_a_list_of_answers_is_opened_item_by_item(fake_service: FakeMammothService) -> None:
    fake_service.responses[_LIST] = _FOLDERS
    rows = [{"resource_type": "label", "resource_id": 707, "object_id": 7}, 5, "x"]
    assert FolderIds(fake_service).open_data(rows, 180) == [
        {"resource_type": "label", "id": 707},
        5,
        "x",
    ]


def test_a_folder_given_as_a_model_is_dumped_before_translation(
    fake_service: FakeMammothService,
) -> None:
    class Model:
        def model_dump(self, mode: str) -> dict[str, Any]:
            assert mode == "json"
            return {"id": 8, "resource_id": 808}

    assert FolderIds(fake_service).open_folder(180, Model()) == {"id": 808}


def test_a_label_tree_node_without_a_project_is_left_alone(
    fake_service: FakeMammothService,
) -> None:
    node = {"type": "label", "id": 7}
    assert FolderIds(fake_service).open_data(node, None) == node
    assert _calls(fake_service, _LIST) == []
