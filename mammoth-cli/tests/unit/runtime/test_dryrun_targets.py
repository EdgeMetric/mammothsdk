"""``--dry-run`` names what a destructive command would change, or fails loud.

Contract (module docstring): a target is never returned without a real display name, read
through the resource's own ``get`` command (its SDK symbol comes from the manifest); a
``destructive`` command with no verified reader fails with ``dry_run_targets_unresolvable``
rather than reporting ``[]``. Response shapes follow the apiv2 models the module cites:
dataset/batch/webhook/... wrap their record, a dataview/parameter/snippet is flat.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.runtime import dryrun_targets as dt
from mammoth_cli.services.testing import FakeMammothService


def sym(command_id: str) -> str:
    record = command_by_id(command_id)
    assert record is not None, command_id
    return str(record["sdk_symbol"])


@pytest.fixture
def svc() -> FakeMammothService:
    return FakeMammothService()


def _calls(svc: FakeMammothService, symbol: str) -> list[dict[str, Any]]:
    return [kwargs for name, kwargs in svc.call_log if name == symbol]


def _targets(svc: FakeMammothService, command: str, **would_call: Any) -> list[dict[str, Any]]:
    return dt.resolve_targets(svc, command, would_call)


# ── named through the resource's own get ──


def test_a_wrapped_record_is_named_from_inside_its_wrapper(svc: FakeMammothService) -> None:
    svc.responses[sym("dataset.get")] = {"dataset": {"id": 7, "name": "Sales 2026"}}
    got = _targets(svc, "dataset.delete", arguments={"dataset_id": 7, "project_id": 180})
    assert got == [{"type": "dataset", "id": 7, "name": "Sales 2026"}]
    assert _calls(svc, sym("dataset.get")) == [{"dataset_id": 7, "project_id": 180}]


def test_a_flat_view_record_is_named_and_read_with_its_dataset_and_project(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt.DATAVIEW_GET] = {"id": 5, "name": "Q1 view"}
    got = _targets(svc, "view.delete", arguments={"view_id": 5, "dataset_id": 7, "project_id": 180})
    assert got == [{"type": "view", "id": 5, "name": "Q1 view"}]
    assert _calls(svc, dt.DATAVIEW_GET) == [{"dataview_id": 5, "dataset_id": 7, "project_id": 180}]


def test_a_view_without_a_known_parent_dataset_is_unresolvable_before_any_read(
    svc: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "view.delete", arguments={"view_id": 5})
    assert excinfo.value.code == dt.CODE_TARGETS_UNRESOLVABLE
    assert excinfo.value.message == (
        "Cannot name what 'view.delete' would change: the parent dataset of view 5 is unknown."
    )
    assert svc.call_log == []


def test_the_dataset_id_may_sit_beside_the_arguments_in_the_reported_call(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt.DATAVIEW_GET] = {"name": "V"}
    got = _targets(svc, "view.delete", arguments={"view_id": 5}, dataset_id=7)
    assert got == [{"type": "view", "id": 5, "name": "V"}]
    assert _calls(svc, dt.DATAVIEW_GET)[0]["dataset_id"] == 7


def test_a_user_is_named_from_first_and_last_name_with_the_id_sent_as_text(
    svc: FakeMammothService,
) -> None:
    svc.responses[sym("workspace.user.get")] = {"first_name": "Ada", "last_name": "Lovelace"}
    got = _targets(svc, "workspace.user.remove", arguments={"user_id": 12})
    assert got == [{"type": "user", "id": 12, "name": "Ada Lovelace"}]
    assert _calls(svc, sym("workspace.user.get")) == [{"user_id": "12"}]


def test_a_user_without_a_name_falls_back_to_the_email(svc: FakeMammothService) -> None:
    svc.responses[sym("workspace.user.get")] = {"first_name": " ", "email": "ada@x.io"}
    got = _targets(svc, "workspace.user.remove", arguments={"user_id": 12})
    assert got[0]["name"] == "ada@x.io"


def test_a_record_with_no_name_is_resource_not_found_with_a_check_hint(
    svc: FakeMammothService,
) -> None:
    svc.responses[sym("dataset.get")] = {"dataset": {"id": 7}}
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "dataset.delete", arguments={"dataset_id": 7})
    error = excinfo.value
    assert (error.code, error.exit_status) == ("resource_not_found", 5)
    assert "Could not resolve the name of dataset 7" in error.message
    assert error.hint == "Check the id with `mammoth dataset get 7`; nothing was changed."
    assert error.details == {"type": "dataset", "id": 7}


def test_a_typed_sdk_model_is_named_by_its_attribute(svc: FakeMammothService) -> None:
    class Typed:
        name = "From a model"

    svc.responses[sym("project.get")] = Typed()
    got = _targets(svc, "project.delete", arguments={"project_id": 180})
    assert got == [{"type": "project", "id": 180, "name": "From a model"}]
    assert _calls(svc, sym("project.get")) == [{"project": 180}]


# ── ids: int, list, comma string; bulk reads ──


def test_ids_accept_an_int_a_list_or_a_comma_text_and_drop_everything_else() -> None:
    assert dt._ids(5) == [5]
    assert dt._ids([1, "2", True, 3]) == [1, 3]
    assert dt._ids("4, 5,x,6") == [4, 5, 6]
    assert dt._ids(True) == []
    assert dt._ids(None) == []
    assert dt._ids({"a": 1}) == []


def test_a_bulk_delete_names_every_id_with_one_bulk_read(svc: FakeMammothService) -> None:
    svc.responses[dt._BULK_SYMBOL] = [
        {"object_id": 1, "name": "Alpha"},
        {"object_id": 2, "name": "Beta"},
    ]
    got = _targets(svc, "dataset.bulk-delete", arguments={"dataset_ids": [1, 2], "project_id": 180})
    assert got == [
        {"type": "dataset", "id": 1, "name": "Alpha"},
        {"type": "dataset", "id": 2, "name": "Beta"},
    ]
    assert _calls(svc, dt._BULK_SYMBOL) == [
        {"items": [("datasource", 1), ("datasource", 2)], "project_id": 180}
    ]
    assert _calls(svc, sym("dataset.get")) == []


def test_an_id_the_bulk_read_misses_is_read_on_its_own_so_its_own_error_surfaces(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt._BULK_SYMBOL] = [{"object_id": 1, "name": "Alpha"}, "junk"]
    svc.responses[sym("dataset.get")] = {"dataset": {"name": "Found alone"}}
    got = _targets(svc, "dataset.bulk-delete", arguments={"dataset_ids": [1, 2]})
    assert [t["name"] for t in got] == ["Alpha", "Found alone"]
    assert _calls(svc, sym("dataset.get")) == [{"dataset_id": 2}]
    # no project in the call: the bulk read carries none either
    assert "project_id" not in _calls(svc, dt._BULK_SYMBOL)[0]


def test_a_single_id_never_uses_the_bulk_route(svc: FakeMammothService) -> None:
    svc.responses[sym("dataset.get")] = {"dataset": {"name": "Solo"}}
    _targets(svc, "dataset.bulk-delete", arguments={"dataset_ids": [9]})
    assert _calls(svc, dt._BULK_SYMBOL) == []


def test_kinds_without_a_bulk_type_are_read_one_by_one(svc: FakeMammothService) -> None:
    svc.responses[sym("webhook.get")] = lambda log: {
        "webhook": {"name": f"hook {log[-1][1]['webhook_id']}"}
    }
    got = _targets(svc, "webhook.delete", arguments={"webhook_id": "3,4"})
    assert [t["name"] for t in got] == ["hook 3", "hook 4"]


def test_a_deleted_folder_is_shown_by_the_id_the_app_opens_it_by(svc: FakeMammothService) -> None:
    svc.responses[sym("folder.get")] = {"name": "Reports"}
    svc.responses["mammoth.api.folders.FoldersAPI.list"] = {
        "folders": [{"id": 31, "resource_id": 900, "name": "Reports"}]
    }
    got = _targets(svc, "folder.delete", arguments={"folder_ids": [31], "project_id": 180})
    assert got == [{"type": "folder", "id": 900, "name": "Reports"}]


# ── fail loud ──


def test_no_explicit_id_means_the_command_may_target_everything_so_it_is_refused(
    svc: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "dataset.delete", arguments={})
    assert excinfo.value.code == "dry_run_targets_unresolvable"
    assert excinfo.value.exit_status == 2
    assert excinfo.value.message == (
        "Cannot name what 'dataset.delete' would change: the call carries no explicit "
        "'dataset_id' ids (it may target every dataset)."
    )
    assert excinfo.value.details == {"command_id": "dataset.delete"}
    assert "--yes" in (excinfo.value.hint or "")


_SPECIAL = {"user.avatar.delete", "dataset.bulk-update", "billing.stripe.held-change.cancel"}
_UNREADABLE = sorted(
    str(record["command_id"])
    for record in load_commands()
    if record.get("mutation_class") == "destructive"
    and record["command_id"] not in dt.COMMAND_TARGETS
    and record["command_id"] not in dt.SUBS
    and record["command_id"] not in dt.CREATES_ONLY
    and record["command_id"] not in _SPECIAL
)


def test_the_sweep_finds_destructive_commands_without_a_verified_reader() -> None:
    assert _UNREADABLE, "if every destructive command has a reader, drop this sweep"


@pytest.mark.parametrize("command_id", _UNREADABLE)
def test_a_destructive_command_without_a_verified_reader_never_reports_empty_targets(
    svc: FakeMammothService, command_id: str
) -> None:
    with pytest.raises(CliError) as excinfo:
        _targets(svc, command_id, arguments={"anything": 1})
    assert excinfo.value.code == dt.CODE_TARGETS_UNRESOLVABLE
    assert excinfo.value.message.endswith("no read command names this command's targets.")
    assert svc.call_log == []


def test_commands_that_only_create_name_nothing(svc: FakeMammothService) -> None:
    assert _targets(svc, "dataset.create", arguments={"name": "x"}) == []


def test_a_non_destructive_dataset_command_names_its_dataset(svc: FakeMammothService) -> None:
    svc.responses[sym("dataset.get")] = {"dataset": {"name": "Sales"}}
    got = _targets(svc, "dataset.update", arguments={"dataset_id": 7})
    assert got == [{"type": "dataset", "id": 7, "name": "Sales"}]


def test_a_non_destructive_view_command_with_a_view_id_names_the_view(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt.DATAVIEW_GET] = {"name": "V"}
    got = _targets(svc, "view.transform.filter", view_id=5, dataset_id=7, arguments={})
    assert got == [{"type": "view", "id": 5, "name": "V"}]


def test_other_non_destructive_commands_name_nothing(svc: FakeMammothService) -> None:
    assert _targets(svc, "view.list", arguments={"dataset_id": 7}) == []
    assert _targets(svc, "project.list", arguments={}) == []
    assert svc.call_log == []


# ── workspace remove-batch: users and pending invites ──


def test_a_user_batch_removal_also_names_pending_invites_by_email(svc: FakeMammothService) -> None:
    svc.responses[sym("workspace.user.get")] = {"first_name": "Ada", "last_name": "L"}
    svc.responses[sym("workspace.invite.list")] = {"invites": [{"id": 4, "email": "new@x.io"}]}
    got = _targets(svc, "workspace.user.remove-batch", arguments={"ids": [12], "invite_ids": [4]})
    assert got == [
        {"type": "user", "id": 12, "name": "Ada L"},
        {"type": "invite", "id": 4, "name": "invite for “new@x.io”"},
    ]


def test_invites_alone_are_enough_to_name_a_batch_removal(svc: FakeMammothService) -> None:
    svc.responses[sym("workspace.invite.list")] = {"invites": [{"id": 4, "email": "new@x.io"}]}
    got = _targets(svc, "workspace.user.remove-batch", arguments={"invite_ids": "4"})
    assert [t["type"] for t in got] == ["invite"]


# ── bulk update / avatar ──


def test_bulk_update_names_the_datasets_in_the_patch_keys_once_each(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt._BULK_SYMBOL] = [
        {"object_id": 3, "name": "Old three"},
        {"object_id": 8, "name": "Old eight"},
    ]
    patch = [
        {"op": "replace", "path": "name", "value": {"3": "New three", "x": "ignored"}},
        {"op": "replace", "path": "name", "value": {"8": "New eight", "3": "again"}},
        "junk",
    ]
    got = _targets(svc, "dataset.bulk-update", arguments={"patch_data": patch})
    assert [(t["id"], t["name"]) for t in got] == [(3, "Old three"), (8, "Old eight")]


def test_bulk_update_without_any_dataset_key_is_unresolvable(svc: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "dataset.bulk-update", arguments={"patch_data": {"op": "replace"}})
    assert excinfo.value.code == dt.CODE_TARGETS_UNRESOLVABLE
    assert "'patch_data' names no dataset" in excinfo.value.message


def test_avatar_delete_names_the_callers_profile_picture(svc: FakeMammothService) -> None:
    svc.responses[sym("user.get")] = {"id": 77, "first_name": "Ada", "last_name": "Lovelace"}
    got = _targets(svc, "user.avatar.delete", arguments={})
    assert got == [{"type": "user avatar", "id": 77, "name": "profile picture of Ada Lovelace"}]


def test_avatar_delete_uses_the_email_when_there_is_no_name_and_fails_with_neither(
    svc: FakeMammothService,
) -> None:
    svc.responses[sym("user.get")] = {"id": 77, "email": "ada@x.io"}
    assert _targets(svc, "user.avatar.delete")[0]["name"] == "profile picture of ada@x.io"
    svc.responses[sym("user.get")] = {"id": 77}
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "user.avatar.delete")
    assert excinfo.value.code == "resource_not_found"


# ── sub-resources named through their parent ──


def test_a_pipeline_step_is_named_with_its_sequence_and_key_under_its_view(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt.DATAVIEW_GET] = {"name": "Q1 view"}
    svc.responses[sym("view.task.get")] = {"params": {"SEQUENCE_NUMBER": 3, "TASK_KEY": "FILTER"}}
    got = _targets(
        svc,
        "view.task.delete",
        arguments={"task_id": 41, "dataview_id": 5, "dataset_id": 7, "project_id": 180},
    )
    assert got == [{"type": "step", "id": 41, "name": "“Q1 view” › step “3: FILTER”"}]
    assert _calls(svc, sym("view.task.get")) == [{"task_id": 41, "dataview_id": 5, "dataset_id": 7}]


def test_a_step_without_a_label_is_named_by_its_id(svc: FakeMammothService) -> None:
    svc.responses[dt.DATAVIEW_GET] = {"name": "Q1 view"}
    svc.responses[sym("view.task.get")] = {"params": {"TASK_KEY": "FILTER"}}  # no sequence
    got = _targets(
        svc, "view.task.delete", arguments={"task_id": 41, "dataview_id": 5, "dataset_id": 7}
    )
    assert got[0]["name"] == "“Q1 view” › step 41"


def test_a_view_parent_with_no_known_dataset_is_found_by_discovery(
    svc: FakeMammothService,
) -> None:
    svc.responses[sym("view.get")] = {"name": "Found view"}
    svc.responses[sym("view.version.get")] = {"name": "v2"}
    got = _targets(svc, "view.version.delete", arguments={"version_id": 2, "dataview_id": 5})
    assert got == [{"type": "version", "id": 2, "name": "“Found view” › version “v2”"}]
    assert _calls(svc, sym("view.get")) == [{"view_id": 5}]


def test_discovery_that_finds_no_name_is_resource_not_found(svc: FakeMammothService) -> None:
    svc.responses[sym("view.get")] = {}
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "view.version.delete", arguments={"version_id": 2, "dataview_id": 5})
    assert excinfo.value.code == "resource_not_found"
    assert excinfo.value.message == (
        "Could not resolve view 5 for the dry-run report: 'ViewsResource.get' found no 'name'."
    )


def test_the_reported_calls_view_and_dataset_ids_scope_the_sub_resource_reads(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt.DATAVIEW_GET] = {"name": "V"}
    svc.responses[sym("view.checkpoint.get")] = {"name": "before merge"}
    got = _targets(
        svc,
        "view.checkpoint.delete",
        dataset_id=7,
        arguments={"checkpoint_id": 2, "dataview_id": 5, "project_id": 180},
    )
    assert got[0]["name"] == "“V” › checkpoint “before merge”"
    assert _calls(svc, sym("view.checkpoint.get")) == [
        {"checkpoint_id": 2, "dataset_id": 7, "dataview_id": 5, "project_id": 180}
    ]


def test_conditional_format_delete_without_a_rule_names_all_of_the_views_rules(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt.DATAVIEW_GET] = {"name": "V"}
    got = _targets(
        svc, "view.conditional-format.delete-all", arguments={"dataview_id": 5, "dataset_id": 7}
    )
    assert got == [
        {"type": "conditional format rule", "id": "all", "name": "“V” › conditional format all"}
    ]


def test_an_unsaved_draft_is_named_under_its_view(svc: FakeMammothService) -> None:
    svc.responses[dt.DATAVIEW_GET] = {"name": "V"}
    got = _targets(
        svc, "view.draft.discard", arguments={"view_id": 5, "dataset_id": 7, "project_id": 180}
    )
    assert got[0]["name"] == "“V” › unsaved draft changes"


def test_one_list_read_serves_every_target_of_a_sub_resource(svc: FakeMammothService) -> None:
    svc.responses[sym("dashboard.tags.list")] = {
        "tags": [{"id": 1, "name": "finance"}, {"id": 2, "name": "ops"}]
    }
    got = _targets(svc, "dashboard.tags.delete", arguments={"tag_id": [1, 2]})
    assert [(t["id"], t["name"]) for t in got] == [
        (1, "tag \u201cfinance\u201d"),
        (2, "tag \u201cops\u201d"),
    ]
    assert len(_calls(svc, sym("dashboard.tags.list"))) == 1


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="_sub_record documents 'a list read serves every target of the call, so it is made "
    "once', but the cache is created per Sub, so tags.merge (two Subs on one list) reads it twice",
)
def test_a_merge_reads_the_tag_list_once_for_both_of_its_tags(svc: FakeMammothService) -> None:
    svc.responses[sym("dashboard.tags.list")] = {
        "tags": [{"id": 1, "name": "finance"}, {"id": 2, "name": "ops"}]
    }
    got = _targets(svc, "dashboard.tags.merge", arguments={"tag_id": 1, "target_id": 2})
    assert [t["name"] for t in got] == ["tag \u201cfinance\u201d", "tag \u201cops\u201d"]
    assert len(_calls(svc, sym("dashboard.tags.list"))) == 1


def test_a_listed_sub_resource_that_is_not_in_the_list_is_resource_not_found(
    svc: FakeMammothService,
) -> None:
    svc.responses[sym("dashboard.tags.list")] = {"tags": [{"id": 1, "name": "finance"}]}
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "dashboard.tags.delete", arguments={"tag_id": 99})
    assert excinfo.value.code == "resource_not_found"
    assert excinfo.value.message == (
        f"Could not resolve tag 99 for the dry-run report: '{sym('dashboard.tags.list')}' "
        "found no 'id'."
    )


def test_a_list_given_as_a_bare_list_or_a_typed_model_is_searched_too(
    svc: FakeMammothService,
) -> None:
    svc.responses[sym("annotation.list")] = [{"id": 5, "text": "see note"}]
    got = _targets(svc, "annotation.delete", arguments={"annotation_id": 5, "project_id": 180})
    assert got[0]["name"] == "annotation “see note”"
    assert _calls(svc, sym("annotation.list")) == [{"project_id": 180}]

    class Page:
        contexts = [{"id": 8, "name": "Finance"}]

    svc.responses[sym("dashboard.context.list")] = Page()
    got = _targets(svc, "dashboard.context.delete", arguments={"context_id": 8})
    assert got[0]["name"] == "context “Finance”"


def test_a_listed_item_matches_by_the_declared_id_field(svc: FakeMammothService) -> None:
    svc.responses[sym("agent.session.list")] = {
        "sessions": [{"session_id": "s-1", "title": "Plan the launch"}]
    }
    got = _targets(svc, "agent.session.delete", arguments={"session_id": "s-1"})
    assert got == [
        {"type": "agent session", "id": "s-1", "name": "agent session “Plan the launch”"}
    ]


def test_a_sub_name_format_may_use_the_calls_own_arguments(svc: FakeMammothService) -> None:
    svc.responses[sym("agent.action.list")] = {"actions": [{"id": 3, "name": "rename"}]}
    got = _targets(svc, "agent.action.delete", arguments={"action_id": 3, "session_id": "s-1"})
    assert got[0]["name"] == "what agent action 3 made: “rename”"
    assert _calls(svc, sym("agent.action.list")) == [{"session_id": "s-1"}]


def test_a_label_takes_the_first_present_path(svc: FakeMammothService) -> None:
    svc.responses[sym("dashboard.template.get")] = {"title": "", "name": "Board", "label": "L"}
    got = _targets(svc, "dashboard.template.delete", arguments={"template_id": 4})
    assert got[0]["name"] == "dashboard template “Board”"
    assert _calls(svc, sym("dashboard.template.get")) == [{"template_id": 4}]


def test_a_sub_with_no_reader_is_named_by_its_id(svc: FakeMammothService) -> None:
    got = _targets(svc, "notification.delete-batch", arguments={"ids": [5, "6", True]})
    assert [t["name"] for t in got] == ["notification 5", "notification 6"]
    assert svc.call_log == []


def test_a_call_with_no_sub_resource_ids_is_unresolvable(svc: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "dashboard.tags.delete", arguments={})
    assert excinfo.value.message == (
        "Cannot name what 'dashboard.tags.delete' would change: the call carries no 'tag_id' "
        "to name."
    )


def test_a_sub_resource_whose_parent_id_is_missing_is_unresolvable(svc: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        _targets(svc, "view.task.delete", arguments={"task_id": 4})
    assert excinfo.value.message.endswith("the view id is unknown.")


def test_ghost_workflow_cleanup_is_named_under_its_project(svc: FakeMammothService) -> None:
    svc.responses[sym("project.get")] = {"name": "Demo"}
    got = _targets(svc, "workflow.cleanup", arguments={"project_id": 180})
    assert got[0]["name"] == "ghost (orphaned skeleton) workflows in “Demo”"


# ── dependents ──


def test_dependents_are_looked_up_for_the_ids_a_delete_names(svc: FakeMammothService) -> None:
    graph = {"7": {"dataviews": [5]}}
    svc.responses[dt._DEPENDENCIES_SYMBOL] = graph
    got = dt.resolve_dependents(
        svc, "dataset.bulk-delete", {"arguments": {"dataset_ids": [7, 8]}}, 180
    )
    assert got is not None
    assert got["checked"] is True
    assert got["resource_ids"] == ["7", "8"]
    assert got["dependencies"] == graph
    assert _calls(svc, dt._DEPENDENCIES_SYMBOL) == [{"project_id": 180, "resource_ids": ["7", "8"]}]


def test_a_step_delete_checks_the_view_whose_dependents_could_break(
    svc: FakeMammothService,
) -> None:
    got = dt.resolve_dependents(
        svc, "view.task.delete", {"dataview_id": 5, "arguments": {"task_id": 1}}, 180
    )
    assert got is not None and got["resource_ids"] == ["5"]


def test_other_commands_have_no_dependents_section(svc: FakeMammothService) -> None:
    assert (
        dt.resolve_dependents(svc, "webhook.delete", {"arguments": {"webhook_id": 1}}, 180) is None
    )


def test_dependents_say_so_when_nothing_was_looked_up(svc: FakeMammothService) -> None:
    no_project = dt.resolve_dependents(
        svc, "dataset.delete", {"arguments": {"dataset_id": 7}}, None
    )
    assert no_project == {
        "checked": False,
        "error": "could not look up dependents: no project is active",
    }
    no_ids = dt.resolve_dependents(svc, "dataset.delete", {"arguments": {}}, 180)
    assert no_ids == {
        "checked": False,
        "error": "could not look up dependents: the call names no resource id",
    }
    assert svc.call_log == []


def test_a_failed_dependents_read_is_reported_unchecked_never_as_none_found(
    svc: FakeMammothService,
) -> None:
    svc.responses[dt._DEPENDENCIES_SYMBOL] = RuntimeError("boom")
    got = dt.resolve_dependents(svc, "view.delete", {"arguments": {"view_id": 5}}, 180)
    assert got == {"checked": False, "resource_ids": ["5"], "error": "RuntimeError: boom"}


def test_a_label_skips_a_present_path_that_is_not_a_non_empty_string(
    svc: FakeMammothService,
) -> None:
    """A truthy number at the first path is not a label; the next path that is text is."""
    svc.responses[sym("dashboard.template.get")] = {"title": 5, "name": "Board", "label": "L"}
    got = _targets(svc, "dashboard.template.delete", arguments={"template_id": 4})
    assert got[0]["name"] == "dashboard template “Board”"
