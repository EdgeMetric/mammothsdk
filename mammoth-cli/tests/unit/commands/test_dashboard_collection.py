"""Unit tests for the ``dashboard collection`` handlers (mvc ``apiv2/collections``).

A live agent turn (10-12) was asked to put the newest dashboard in "QA
collection" and answered that dashboards have only tags: the CLI had no
collection commands although the web app has collections.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.dryrun_targets import resolve_targets
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_SDK = "mammoth.api.dashboards.DashboardsAPI."
_LIST = _SDK + "list_collections"
_GET = _SDK + "get_collection"
_CREATE = _SDK + "create_collection"
_UPDATE = _SDK + "update_collection"
_DELETE = _SDK + "delete_collection"
_ADD = _SDK + "add_to_collection"
_REMOVE = _SDK + "remove_from_collection"

# Admission checks a field's type before the handler checks its value.
_BAD_VALUE = {"invalid_argument", "invalid_input_field_type"}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _doc(tmp_path: Path, payload: dict[str, object]) -> str:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _detail(**extra: object) -> dict[str, object]:
    return {
        "id": 12,
        "name": "QA collection",
        "project_id": 180,
        "role": "manager",
        "dashboard_count": 1,
        "dashboards": [{"dashboard_id": 123, "title": "Revenue", "position": 0}],
        **extra,
    }


# -- manifest and wiring -------------------------------------------------------


@pytest.mark.parametrize(
    ("verb", "mutation_class", "confirmation"),
    [
        ("list", "read", "none"),
        ("get", "read", "none"),
        ("create", "benign_mutation", "none"),
        ("update", "benign_mutation", "none"),
        ("add", "benign_mutation", "none"),
        ("remove", "benign_mutation", "none"),
        ("delete", "destructive", "prompt_or_yes"),
    ],
)
def test_each_command_carries_its_policy_and_handler(
    verb: str, mutation_class: str, confirmation: str
) -> None:
    command_id = f"dashboard.collection.{verb}"
    record = command_by_id(command_id)
    assert record is not None
    assert record["command_path"] == f"dashboard collection {verb}"
    assert record["mutation_class"] == mutation_class
    assert record["confirmation"] == confirmation
    assert (
        record["sdk_symbol"]
        == _SDK
        + {
            "list": "list_collections",
            "get": "get_collection",
            "create": "create_collection",
            "update": "update_collection",
            "delete": "delete_collection",
            "add": "add_to_collection",
            "remove": "remove_from_collection",
        }[verb]
    )
    assert command_id in HANDLERS


def test_the_list_says_dashboards_have_collections_as_well_as_tags() -> None:
    record = command_by_id("dashboard.collection.list")
    assert record is not None
    assert "as well as tags" in str(record["known_restrictions"])


# -- list / get ----------------------------------------------------------------


def test_list_reads_every_collection(fake_service: FakeMammothService) -> None:
    fake_service.responses[_LIST] = {"collections": [_detail()]}
    result, meta = dashboard_cmd.dashboard_collection_list(_inv("dashboard.collection.list"))
    assert fake_service.call_log == [(_LIST, {})]
    assert result["collections"][0]["name"] == "QA collection"
    assert meta["project_id"] is None


def test_list_with_a_dashboard_reads_the_collections_holding_it(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_LIST] = {"collections": []}
    dashboard_cmd.dashboard_collection_list(_inv("dashboard.collection.list", extra_args=["123"]))
    assert fake_service.call_log == [(_LIST, {"dashboard_id": 123})]


def test_get_reads_one_collection(fake_service: FakeMammothService) -> None:
    fake_service.responses[_GET] = _detail()
    result, _ = dashboard_cmd.dashboard_collection_get(
        _inv("dashboard.collection.get", extra_args=["12"])
    )
    assert fake_service.call_log == [(_GET, {"collection_id": 12})]
    assert result["dashboards"][0]["dashboard_id"] == 123


@pytest.mark.parametrize("raw", ["0", "-3"])
def test_get_refuses_a_non_positive_id(fake_service: FakeMammothService, raw: str) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_get(_inv("dashboard.collection.get", extra_args=[raw]))
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


# -- create --------------------------------------------------------------------


def test_create_takes_the_name_and_the_dashboards(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CREATE] = _detail()
    result, meta = dashboard_cmd.dashboard_collection_create(
        _inv(
            "dashboard.collection.create",
            input_file=_doc(
                tmp_path, {"name": " QA collection ", "dashboard_ids": [123], "project_id": 180}
            ),
        )
    )
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "name": "QA collection",
                "project_id": 180,
                "description": None,
                "dashboard_ids": [123],
            },
        )
    ]
    assert result["id"] == 12
    assert meta["project_id"] == 180


def test_create_falls_back_to_the_active_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CREATE] = _detail()
    dashboard_cmd.dashboard_collection_create(
        _inv(
            "dashboard.collection.create",
            project=181,
            input_file=_doc(tmp_path, {"name": "QA collection", "description": "For QA"}),
        )
    )
    assert fake_service.call_log == [
        (
            _CREATE,
            {
                "name": "QA collection",
                "project_id": 181,
                "description": "For QA",
                "dashboard_ids": [],
            },
        )
    ]


def test_create_without_any_project_says_where_to_find_one(
    fake_service: FakeMammothService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(dashboard_cmd, "resolved_project", lambda _invocation: None)
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_create(
            _inv(
                "dashboard.collection.create",
                input_file=_doc(tmp_path, {"name": "QA collection"}),
            )
        )
    assert excinfo.value.code == "missing_field"
    assert "dashboard list" in (excinfo.value.hint or "")
    assert fake_service.call_log == []


@pytest.mark.parametrize(
    ("document", "code"),
    [
        ({"project_id": 180}, "missing_field"),
        ({"name": "   ", "project_id": 180}, "invalid_argument"),
        ({"name": "x" * 121, "project_id": 180}, "invalid_argument"),
        ({"name": "QA", "project_id": 180, "dashboard_ids": "123"}, "invalid_argument"),
        ({"name": "QA", "project_id": 180, "dashboard_ids": [0]}, "invalid_argument"),
        ({"name": "QA", "project_id": 0}, "invalid_argument"),
        ({"name": "QA", "project_id": 180, "description": "d" * 2001}, "invalid_argument"),
    ],
)
def test_create_refuses_bad_input_without_a_request(
    fake_service: FakeMammothService,
    tmp_path: Path,
    document: dict[str, object],
    code: str,
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_create(
            _inv(
                "dashboard.collection.create",
                input_file=_doc(tmp_path, document),
            )
        )
    assert excinfo.value.code in ({code} if code != "invalid_argument" else _BAD_VALUE)
    assert fake_service.call_log == []


def test_create_refuses_an_unknown_field(fake_service: FakeMammothService, tmp_path: Path) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_create(
            _inv(
                "dashboard.collection.create",
                input_file=_doc(tmp_path, {"name": "QA", "project_id": 180, "notify": True}),
            )
        )
    assert excinfo.value.code == "unknown_input_field"
    assert fake_service.call_log == []


def test_create_passes_a_dashboard_from_another_project_error_through(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CREATE] = CliError(
        code="api_error",
        message="A collection holds only its own project's dashboards.",
        details={"backend_code": "4COLL002"},
    )
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_create(
            _inv(
                "dashboard.collection.create",
                input_file=_doc(
                    tmp_path, {"name": "QA", "project_id": 180, "dashboard_ids": [999]}
                ),
            )
        )
    assert excinfo.value.details["backend_code"] == "4COLL002"


# -- update --------------------------------------------------------------------


def test_update_sends_only_the_fields_given(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_UPDATE] = _detail(name="Board pack")
    result, _ = dashboard_cmd.dashboard_collection_update(
        _inv(
            "dashboard.collection.update",
            extra_args=["12"],
            input_file=_doc(
                tmp_path,
                {"name": " Board pack ", "order": [124, 123], "tab_labels": {"123": "Sales"}},
            ),
        )
    )
    assert fake_service.call_log == [
        (
            _UPDATE,
            {
                "collection_id": 12,
                "name": "Board pack",
                "order": [124, 123],
                "tab_labels": {"123": "Sales"},
            },
        )
    ]
    assert result["name"] == "Board pack"


def test_update_with_an_empty_description_clears_it(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_UPDATE] = _detail()
    dashboard_cmd.dashboard_collection_update(
        _inv(
            "dashboard.collection.update",
            extra_args=["12"],
            input_file=_doc(tmp_path, {"description": ""}),
        )
    )
    assert fake_service.call_log == [(_UPDATE, {"collection_id": 12, "description": ""})]


@pytest.mark.parametrize(
    ("document", "code"),
    [
        ({}, "missing_field"),
        ({"name": "  "}, "invalid_argument"),
        ({"order": []}, "invalid_argument"),
        ({"tab_labels": {"Sales": "x"}}, "invalid_argument"),
    ],
)
def test_update_refuses_bad_input_without_a_request(
    fake_service: FakeMammothService, tmp_path: Path, document: dict[str, object], code: str
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_update(
            _inv(
                "dashboard.collection.update",
                extra_args=["12"],
                input_file=_doc(tmp_path, document),
            )
        )
    assert excinfo.value.code in ({code} if code != "invalid_argument" else _BAD_VALUE)
    assert fake_service.call_log == []


# -- add / remove ----------------------------------------------------------------


def test_add_reports_what_was_added_and_what_was_already_in(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_ADD] = {"added": [124], "notified": 0}
    result, _ = dashboard_cmd.dashboard_collection_add(
        _inv(
            "dashboard.collection.add",
            extra_args=["12"],
            input_file=_doc(tmp_path, {"dashboard_ids": [123, 124]}),
        )
    )
    assert fake_service.call_log == [(_ADD, {"collection_id": 12, "dashboard_ids": [123, 124]})]
    assert result == {"collection_id": 12, "added": [124], "already_in": [123]}


def test_add_needs_no_confirmation(fake_service: FakeMammothService, tmp_path: Path) -> None:
    fake_service.responses[_ADD] = {"added": [123], "notified": 0}
    dashboard_cmd.dashboard_collection_add(
        _inv(
            "dashboard.collection.add",
            extra_args=["12"],
            input_file=_doc(tmp_path, {"dashboard_ids": [123]}),
            no_input=True,
        )
    )
    assert len(fake_service.call_log) == 1


@pytest.mark.parametrize(
    ("document", "code"),
    [
        ({}, "missing_field"),
        ({"dashboard_ids": []}, "invalid_argument"),
        ({"dashboard_ids": [True]}, "invalid_argument"),
    ],
)
def test_add_refuses_bad_ids_without_a_request(
    fake_service: FakeMammothService, tmp_path: Path, document: dict[str, object], code: str
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_add(
            _inv(
                "dashboard.collection.add",
                extra_args=["12"],
                input_file=_doc(tmp_path, document),
            )
        )
    assert excinfo.value.code in ({code} if code != "invalid_argument" else _BAD_VALUE)
    assert fake_service.call_log == []


def test_add_refuses_a_notify_field(fake_service: FakeMammothService, tmp_path: Path) -> None:
    # Emailing the collection's people is a message sent for the user: not here.
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_add(
            _inv(
                "dashboard.collection.add",
                extra_args=["12"],
                input_file=_doc(tmp_path, {"dashboard_ids": [123], "notify": True}),
            )
        )
    assert excinfo.value.code == "unknown_input_field"
    assert fake_service.call_log == []


def test_remove_takes_one_dashboard_out(fake_service: FakeMammothService) -> None:
    fake_service.responses[_REMOVE] = None
    result, _ = dashboard_cmd.dashboard_collection_remove(
        _inv("dashboard.collection.remove", extra_args=["12", "123"], no_input=True)
    )
    assert fake_service.call_log == [(_REMOVE, {"collection_id": 12, "dashboard_id": 123})]
    assert result == {"collection_id": 12, "dashboard_id": 123, "removed": True}


def test_remove_requires_the_dashboard_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_remove(
            _inv("dashboard.collection.remove", extra_args=["12"])
        )
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


# -- delete ----------------------------------------------------------------------


def test_delete_needs_yes_without_a_terminal(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_collection_delete(
            _inv("dashboard.collection.delete", extra_args=["12"], no_input=True)
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_with_yes_deletes_the_collection(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DELETE] = None
    result, _ = dashboard_cmd.dashboard_collection_delete(
        _inv("dashboard.collection.delete", extra_args=["12"], yes=True)
    )
    assert fake_service.call_log == [(_DELETE, {"collection_id": 12})]
    assert result == {"collection_id": 12, "deleted": True}


def test_a_delete_dry_run_names_the_collection(fake_service: FakeMammothService) -> None:
    fake_service.responses[_GET] = _detail()
    targets = resolve_targets(
        fake_service,
        "dashboard.collection.delete",
        {"arguments": {"collection_id": 12}},
    )
    assert targets == [{"type": "collection", "id": 12, "name": "QA collection"}]
