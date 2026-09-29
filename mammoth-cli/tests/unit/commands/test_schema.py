"""Unit tests for the R7 schema-discovery enrichment.

``mammoth schema get`` must expose enough for an agent to build a valid
invocation without reading source: each accepted field's type, enum values
(when it is an enum), and default; the command's real positional arguments
(derived from :mod:`mammoth_cli.services.positionals`, not the manifest's
placeholder empty list); and one complete, runnable example command line.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

import pytest
import yaml

from mammoth_cli.commands.schema import brief_schema, find_schemas, get_schema, runnable_example
from mammoth_cli.services.positionals import positionals_for

_BULK_REPLACE = "view.transform.bulk-replace"
_TEXT_TRANSFORM = "view.transform.text"
_MATH_TRANSFORM = "view.transform.math"
_PROJECT_DELETE = "project.delete"
ROOT = Path(__file__).parents[3]


def test_enum_field_exposes_its_member_values() -> None:
    """A command with an enum-typed field ('case') reports its values."""
    schema = get_schema(_TEXT_TRANSFORM)
    assert schema is not None
    fields = {field["name"]: field for field in schema["accepted_fields"]}
    assert fields["case"]["type"] == "TextCase"
    assert fields["case"]["enum"] == ["UPPER", "LOWER", "TITLE"]
    assert fields["case"]["required"] is False


def test_accepted_fields_report_type_and_default() -> None:
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    fields = {field["name"]: field for field in schema["accepted_fields"]}
    assert fields["match_case"]["type"] == "bool"
    assert fields["match_case"]["default"] is True
    assert fields["columns"]["required"] is True
    assert fields["columns"]["enum"] is None


def test_transform_schema_advertises_exact_parent_dataset_context() -> None:
    schema = get_schema(_MATH_TRANSFORM)
    assert schema is not None
    fields = {field["name"]: field for field in schema["accepted_fields"]}
    assert fields["dataset_id"]["type"] == "int"
    assert fields["dataset_id"]["required"] is False
    assert fields["dataset_id"]["schema"]["anyOf"][0]["minimum"] == 1


def test_export_dataset_positional_disambiguates_source_parent_from_target() -> None:
    """WPP evidence (c38/c39): an agent passed the 2nd positional expecting it
    to name the destination dataset, then hit the same resource_not_found even
    with an explicit dataset -- because that positional is the SOURCE view's
    own parent, and the destination is the separate 'target_ds_id' field."""
    schema = get_schema("view.export.dataset")
    assert schema is not None
    positionals = {p["name"]: p for p in schema["positionals"]}
    help_text = positionals["dataset_id"]["help"]
    assert "not the destination" in help_text
    assert "target_ds_id" in help_text


def test_bulk_replace_exposes_the_required_view_id_positional() -> None:
    """bulk-replace's positional (the view id) was previously invisible."""
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    positionals = schema["positionals"]
    assert len(positionals) == 1
    assert positionals[0]["name"] == "view_id"
    assert positionals[0]["type"] == "int"
    assert positionals[0]["required"] is True
    assert positionals[0]["metavar"] == "VIEW_ID"


def test_bulk_replace_exposes_the_typed_mapping_structure() -> None:
    """The 'mapping' field's type names BulkReplaceMapping, not opaquely."""
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    fields = {field["name"]: field for field in schema["accepted_fields"]}
    assert fields["mapping"]["type"] == "list[BulkReplaceMapping]"
    item = fields["mapping"]["schema"]["items"]
    assert item["required"] == ["search", "replace"]
    assert item["properties"]["search"]["items"]["type"] == "string"


def test_bulk_replace_runnable_example_includes_the_positional_and_input() -> None:
    schema = get_schema(_BULK_REPLACE)
    assert schema is not None
    example = schema["runnable_example"]
    assert example is not None
    assert example.startswith("mammoth view transform bulk-replace 123 ")
    assert "--input" in example
    assert "--output json" not in example
    tokens = shlex.split(example)
    document = json.loads(tokens[tokens.index("--input") + 1])
    assert document["mapping"] == [{"search": ["sample"], "replace": "sample"}]


def test_optional_positional_command_has_no_required_positional_in_example() -> None:
    """'project delete' has an optional positional; the example need not force it."""
    schema = get_schema(_PROJECT_DELETE)
    assert schema is not None
    positionals = schema["positionals"]
    assert len(positionals) == 1
    assert positionals[0]["required"] is False
    assert all(field["name"] != "project_id" for field in schema["accepted_fields"])
    assert "project_id" not in schema["runnable_example"]


def test_fallback_positional_is_accepted_but_not_duplicated_in_example() -> None:
    schema = get_schema("project.create")
    assert schema is not None
    assert "name" in {field["name"] for field in schema["accepted_fields"]}
    tokens = shlex.split(schema["runnable_example"])
    assert tokens[:4] == ["mammoth", "project", "create", "Revenue report"]
    assert "--input" not in tokens


def test_exportable_config_schema_is_exact_one_of_and_view_centric() -> None:
    get = get_schema("view.exportable-config.get")
    apply = get_schema("view.exportable-config.apply")
    assert get is not None and apply is not None
    assert [p["name"] for p in get["positionals"]] == ["view_id", "dataset_id"]
    assert {field["name"]: field["required"] for field in get["accepted_fields"]} == {
        "dataset_id": False
    }
    assert get["input_schema"]["required"] == []
    assert "dataview_id" not in get["input_schema"]["properties"]
    schema = apply["input_schema"]
    assert {field["name"]: field["required"] for field in apply["accepted_fields"]}[
        "dataset_id"
    ] is False
    assert "dataset_id" in schema["properties"]
    assert schema["oneOf"] == [
        {"required": ["items"], "not": {"required": ["config"]}},
        {"required": ["config"], "not": {"required": ["items"]}},
    ]
    config_properties = schema["properties"]["config"]["properties"]
    assert config_properties["tasks"]["type"] == [
        "array",
        "null",
    ]
    assert config_properties["tasks"]["items"] == {"type": "object"}
    assert config_properties["name"]["type"] == [
        "string",
        "null",
    ]
    example = shlex.split(apply["runnable_example"])
    assert example[:5] == ["mammoth", "view", "exportable-config", "apply", "123"]
    assert "--yes" in example and example[example.index("--confirm") + 1] == "123"


def test_batch_data_schema_exposes_release_paging_bounds() -> None:
    schema = get_schema("dataset.batch-data")
    assert schema is not None
    assert schema["input_schema"]["properties"]["limit"]["minimum"] == 0
    assert schema["input_schema"]["properties"]["limit"]["maximum"] == 100
    assert schema["input_schema"]["properties"]["offset"]["minimum"] == 0


def test_unknown_command_returns_none() -> None:
    assert get_schema("nope.nope") is None


def test_schema_get_exposes_dispatch_policy_and_exact_sensitive_scope() -> None:
    project_admin = get_schema("project.user.update")
    share = get_schema("data-app.share")
    apply = get_schema("view.exportable-config.apply")
    assert project_admin is not None and share is not None and apply is not None

    assert (project_admin["mutation_class"], project_admin["confirmation"]) == (
        "high_impact",
        "yes_always",
    )
    assert project_admin["scope_requirements"]["required_context"] == ["project_id"]
    assert share["scope_requirements"] == {
        "kind": "workspace",
        "required_context": ["workspace_id"],
        "target_fields": ["data_app_id"],
        "target_rule": "data_app_id is a required positional",
    }
    assert (apply["mutation_class"], apply["confirmation"], apply["wait_policy"]) == (
        "reversible_pipeline",
        "confirm_target",
        "returns_job",
    )
    assert apply["scope_requirements"]["target_fields"] == ["view_id", "dataset_id"]
    assert "--yes" in shlex.split(project_admin["agent_example"])
    assert "--yes" in shlex.split(share["agent_example"])
    assert "--yes" in shlex.split(project_admin["runnable_example"])
    assert "--yes" in shlex.split(share["runnable_example"])


def test_agent_transform_language_finds_typed_routes() -> None:
    assert "view.transform.discard-duplicates" in {
        item["command_id"] for item in find_schemas("duplicate")["matches"]
    }
    assert "view.transform.convert-type" in {
        item["command_id"] for item in find_schemas("cast numeric type")["matches"]
    }
    assert "view.transform.fill-missing" in {
        item["command_id"] for item in find_schemas("fill missing")["matches"]
    }
    assert "view.transform.join" in {
        item["command_id"] for item in find_schemas("join blend")["matches"]
    }


def test_bind_parameter_finds_the_filter_transform() -> None:
    """WPP evidence: an agent asked to 'filter by parameter' or 'bind a
    parameter' to a condition value never reached view.transform.filter,
    which is the only place that value can be a parameter binding marker."""
    assert "view.transform.filter" in {
        item["command_id"] for item in find_schemas("filter by parameter")["matches"]
    }
    assert "view.transform.filter" in {
        item["command_id"] for item in find_schemas("bind parameter to condition")["matches"]
    }


def test_run_execute_apply_refresh_find_pipeline_rerun_and_draft_submit() -> None:
    """Synonyms for 'run/execute/apply/refresh the pipeline tasks' must reach
    view.pipeline.rerun (re-run from a point in the task sequence) and
    view.draft.submit (apply a pending draft)."""
    for query in ("run pipeline", "execute pipeline tasks", "refresh pipeline", "recompute view"):
        matches = {item["command_id"] for item in find_schemas(query)["matches"]}
        assert "view.pipeline.rerun" in matches, query
    for query in ("apply draft", "apply pending changes"):
        matches = {item["command_id"] for item in find_schemas(query)["matches"]}
        assert "view.draft.submit" in matches, query


def test_append_rows_between_datasets_finds_view_export_dataset() -> None:
    """A cold agent must find the row-stacking route, not just file.upload.

    'append rows from one dataset into another dataset' previously matched
    only file.upload (which needs a local file); an agent that has both
    sources already in Mammoth would wrongly conclude row-stacking is
    impossible. view.export.dataset (target_ds_id + save_as_mode
    APPEND_TO_DS) must also surface.
    """
    matches = {
        item["command_id"]
        for item in find_schemas("append rows from one dataset into another dataset")["matches"]
    }
    assert "view.export.dataset" in matches


def test_email_a_view_as_a_csv_attachment_finds_automation_create() -> None:
    """A scheduled email action attaches each selected view as a CSV
    (backend: ``generate_csv_files_for_attachment``); a cold agent phrasing
    that goal in plain words must still land on automation.create, not just
    on a synonym-adjacent export command.
    """
    matches = {
        item["command_id"]
        for item in find_schemas("email a view as a csv attachment every week")["matches"]
    }
    assert "automation.create" in matches


_EXPORT_DESTINATION_NATURAL_QUERIES = {
    "view.export.azure-blob": "export to azure blob storage",
    "view.export.bigquery": "export to big query",
    "view.export.csv": "export to csv file",
    "view.export.dataset": "copy rows into another dataset",
    "view.export.elasticsearch": "export to elastic search",
    "view.export.email": "email the export",
    "view.export.ftp": "export via ftp",
    "view.export.managed-s3": "export to s3 bucket",
    "view.export.mssql": "export to sql server",
    "view.export.mysql": "export to mysql database",
    "view.export.onedrive": "export to one drive",
    "view.export.postgres": "export to postgres database",
    "view.export.powerbi": "publish to power bi workspace",
    "view.export.publish-db": "publish live database connection",
    "view.export.publish-db-update": "refresh the live database connection",
    "view.export.redshift": "export to redshift warehouse",
    "view.export.rest": "export data to a rest endpoint",
    "view.export.sftp": "export via sftp",
    "view.export.sharepoint": "export to share point",
    "view.export.tableau": "export to tableau server",
}


def test_every_export_destination_is_covered_by_this_test() -> None:
    """Guards the fixture itself: a new view.export.* destination command
    must get a natural-spelling case here, not silently go untested."""
    destinations = {
        item["command_id"]
        for item in find_schemas("export")["matches"]
        if item["command_id"].startswith("view.export.")
        and item["command_id"].split(".")[-1] not in {"create", "get", "list", "update", "delete"}
    }
    assert destinations <= set(_EXPORT_DESTINATION_NATURAL_QUERIES)


@pytest.mark.parametrize(
    ("command_id", "query"), sorted(_EXPORT_DESTINATION_NATURAL_QUERIES.items())
)
def test_export_destination_natural_spelling_ranks_it_first(command_id: str, query: str) -> None:
    """T1-H-005: 'Power BI', 'publish to Power BI workspace' and 'export data
    to BI' all returned no match, despite view.export.powerbi existing.  Every
    typed export destination must be reachable by how a user actually names
    it, not only by Mammoth's own (sometimes compound, unhyphenated) route
    spelling.
    """
    matches = [item["command_id"] for item in find_schemas(query)["matches"]]
    assert matches, f"no full match for {query!r} (wanted {command_id})"
    assert matches[0] == command_id, f"{query!r} -> {matches}, wanted {command_id} first"


def test_invite_user_intent_ranks_workspace_user_add_first() -> None:
    """T1-K-001: this query led an agent to support.workspace.user.add /
    support.workspace.user.list (Mammoth-operator commands that act on
    another workspace) instead of the caller's own workspace.user.add.
    """
    matches = [
        item["command_id"]
        for item in find_schemas("invite user to workspace and assign editor role")["matches"]
    ]
    assert matches, "no full match for the invite-user query"
    assert matches[0] == "workspace.user.add", matches


def test_active_api_keys_intent_ranks_client_app_above_external_key() -> None:
    """Live-eval evidence: 'what API keys do we have active right now?' only
    surfaced external-key.list (LLM provider keys), never client-app.list --
    which IS the product's API key/secret credential for a script or
    integration to call Mammoth. client-app.list must rank first for this
    intent, and ahead of external-key.list wherever both appear.
    """
    matches = [item["command_id"] for item in find_schemas("list active API keys")["matches"]]
    assert "client-app.list" in matches, matches
    assert matches[0] == "client-app.list", matches
    if "external-key.list" in matches:
        assert matches.index("client-app.list") < matches.index("external-key.list"), matches


def test_past_conversation_intent_ranks_agent_session_first() -> None:
    """In-product-agent evidence: `schema find "conversation history previous
    messages chat conversations asked earlier this week"` never matched
    `agent.session.list`/`agent.session.messages` -- nothing in either
    command's own text says "conversation", "chat", "history", or "asked" --
    so the agent never ran `agent session list`, which exists and works.
    """
    matches = [
        item["command_id"]
        for item in find_schemas(
            "conversation history previous messages chat conversations asked earlier this week"
        )["matches"]
    ]
    assert matches, "no full match for the past-conversation query"
    assert matches[0] == "agent.session.list", matches
    assert "agent.session.messages" in matches, matches


def test_what_did_i_ask_earlier_ranks_agent_session_list_first() -> None:
    result = find_schemas("what did I ask you about earlier this week")
    top = result["matches"] or result.get("suggestions", [])
    assert top, "no match or suggestion for the past-conversation query"
    assert top[0]["command_id"] == "agent.session.list", top


def test_pick_up_where_we_left_off_reaches_agent_session_list() -> None:
    """Live-eval evidence (T1-A-04): 'pick up where we left off last time on
    the orders' -- the model searched 'recent project activity' and
    'activity list' instead. activity.list may still rank for some of
    these, but agent.session.list (the actual past-conversation lookup)
    must be at or near the top, not absent.
    """
    for query in (
        "pick up where we left off last time",
        "continue where I left off on the orders",
        "resume my previous conversation about orders",
        "what did we talk about earlier in this chat",
    ):
        matches = [item["command_id"] for item in find_schemas(query)["matches"]]
        assert matches, f"no full match for {query!r}"
        assert "agent.session.list" in matches[:3], f"{query!r} -> {matches}"


def test_undo_dashboard_intent_reaches_chat_history() -> None:
    """Live-eval evidence (T1-D-09): 'I messed up the board, put it back to how
    it was before' -- dashboard.canvas.restore needs a target_sequence, and
    dashboard.chat.history is the command that lists every saved version
    (revisions[]) a sequence can be picked from, but neither 'undo', 'put back',
    'previous version', 'before', nor 'revert' reached it.
    """
    for query in (
        "put the dashboard back to how it was before",
        "undo my last change to the board",
        "revert the dashboard to a previous version",
    ):
        matches = [item["command_id"] for item in find_schemas(query)["matches"]]
        assert "dashboard.chat.history" in matches, f"{query!r} -> {matches}"


def test_matched_purpose_text_is_returned_so_the_caller_knows_why_it_matched() -> None:
    """Live-eval evidence (T1-I-07): 'custom internal API sources' ranked
    connector.ai.chat first via its hidden purpose text ("connect our own
    internal custom api build a connector for an unsupported source"), but
    schema find never handed that text back -- only command_id/command_path/
    agent_example/matched_terms -- so the model read it as "ask the AI a
    question" and never explained the generic/custom-connector route. Every
    match must now carry why it matched.
    """
    result = find_schemas("custom internal API sources")
    by_id = {item["command_id"]: item for item in result["suggestions"]}
    assert "connector.ai.chat" in by_id, result["suggestions"]
    matched_on = by_id["connector.ai.chat"]["matched_on"]
    assert "build a connector for an unsupported source" in matched_on, matched_on


def test_hint_presents_suggestions_as_candidates_when_present() -> None:
    """Live-eval evidence (T1-R-06): 'automation trigger on new file in folder;
    scheduled weekly automation append data' returned zero full matches, and
    the agent stopped at the "No command matched every word" hint even though
    'suggestions' already held automation.create -- the framing read as a
    dead end rather than "try one of these". A query with suggestions must
    get a hint that says to use them; only a query with NO suggestions at all
    gets the harsher "try fewer or other words" framing.
    """
    with_suggestions = find_schemas(
        "automation trigger on new file in folder; scheduled weekly automation append data"
    )
    assert with_suggestions["total_matches"] == 0
    assert with_suggestions["suggestions"]
    assert "automation.create" in {m["command_id"] for m in with_suggestions["suggestions"]}
    assert "candidates" in with_suggestions["hint"]
    assert "No command matched every word" not in with_suggestions["hint"]

    no_suggestions = find_schemas("zzqxwv frobnicate glarbnak")
    assert no_suggestions["total_matches"] == 0
    assert not no_suggestions["suggestions"]
    assert "candidates" not in no_suggestions["hint"]


def test_or_is_a_discovery_stopword_so_import_workbook_still_matches() -> None:
    """Live-eval evidence (T1-D-06): 'import Power BI or Tableau reports; export
    dashboard or board as PDF' -- the incidental conjunction 'or' was not a
    discovery stopword, so it became a required term; dashboard.import-workbook's
    purpose text has no literal 'or' and dropped out, while dashboard.bi-export/
    bi-preflight won by accident (their text happens to contain 'desktop or
    tableau desktop').
    """
    matches = [
        item["command_id"] for item in find_schemas("import Power BI or Tableau reports")["matches"]
    ]
    assert "dashboard.import-workbook" in matches, matches


def test_row_level_security_intent_reaches_dashboard_rls() -> None:
    """Live-eval evidence (T1-D-03): 'row-level security' / 'per-user or
    row-level region security' never matched any dashboard.rls.* command --
    none had any discovery-purpose text at all.
    """
    matches = [
        item["command_id"] for item in find_schemas("row-level security per manager")["matches"]
    ]
    assert any(m.startswith("dashboard.rls.") for m in matches), matches


def test_dashboard_template_intent_reaches_template_family() -> None:
    """Live-eval evidence (T1-D-12): 'list browse available dashboard templates
    styles; apply template to current dashboard' returned 0 matches --
    dashboard.template.* had no discovery-purpose text at all.
    """
    matches = [
        item["command_id"]
        for item in find_schemas("list browse available dashboard templates styles")["matches"]
    ]
    assert any(m.startswith("dashboard.template") for m in matches), matches


def test_publish_dashboard_intent_reaches_dashboard_action() -> None:
    """Live-eval evidence (T1-D-15): 'publish dashboard' / 'make it live' never
    surfaced dashboard.action (the actual publish step dashboard.share depends
    on) among 12 near-misses -- it had no discovery-purpose text.
    """
    matches = [
        item["command_id"] for item in find_schemas("publish dashboard make it live")["matches"]
    ]
    assert "dashboard.action" in matches, matches


def test_hedged_view_or_dashboard_bi_export_still_matches() -> None:
    """Live-eval evidence (T1-D-22): 'publish a dashboard or its underlying view
    to Power BI' matched only view.export.powerbi (the raw ODBC connector) --
    dashboard.bi-export/bi-preflight missed only because their purpose text
    never says 'view', so the hedge word knocked them out of the strict
    all-terms gate.
    """
    matches = [
        item["command_id"]
        for item in find_schemas("publish a dashboard or its underlying view to Power BI")[
            "matches"
        ]
    ]
    assert "dashboard.bi-export" in matches or "dashboard.bi-preflight" in matches, matches


def test_url_import_intent_reaches_dataset_create() -> None:
    """Live-eval evidence (T1-I-16): 'import data from a public URL or JSON API
    into a dataset' / 'fetch or retrieve JSON from public URL into dataset'
    never matched dataset.create (ds_creation_type=weburl), which has no
    discovery-purpose text at all -- even though the capability exists and
    works once found.
    """
    for query in (
        "import data from a public URL into a dataset",
        "fetch or retrieve JSON from a public URL into a dataset",
    ):
        matches = [item["command_id"] for item in find_schemas(query)["matches"]]
        assert "dataset.create" in matches, f"{query!r} -> {matches}"


def test_alert_on_row_match_reaches_checkpoint_create() -> None:
    """Live-eval evidence (T1-R-02): 'alert me when a row matches a condition' /
    'notify me if a value changes' should surface view.checkpoint.create
    (checkpoint_type=alert) as an automation-adjacent option, not just
    automation.create.
    """
    for query in (
        "alert me when a row matches a condition",
        "notify me if a value changes",
    ):
        matches = [item["command_id"] for item in find_schemas(query)["matches"]]
        assert "view.checkpoint.create" in matches, f"{query!r} -> {matches}"


def test_new_file_in_folder_trigger_reaches_automation_create() -> None:
    """Live-eval evidence (T1-R-06): 'automation trigger on new file in folder;
    scheduled weekly automation append data' returned no match -- the agent
    lacked a discovered path for a new-file-arrives trigger.
    """
    matches = [
        item["command_id"]
        for item in find_schemas("trigger automation on new file in a folder")["matches"]
    ]
    assert "automation.create" in matches, matches


def test_plan_storage_intent_reaches_billing_plan_commands() -> None:
    """Live-eval evidence (T1-W-06): 'what plan are we on and how much storage
    does it include' / 'current subscription plan tier for workspace; billing
    plan and storage allowance' returned 'No command matched every word' twice
    -- billing.chargebee-plan/billing.subscription.get had no discovery text
    for plan/subscription/storage-allowance phrasing.
    """
    matches = [
        item["command_id"]
        for item in find_schemas(
            "current subscription plan tier for workspace; billing plan and storage allowance"
        )["matches"]
    ]
    assert "billing.chargebee-plan" in matches or "billing.subscription.get" in matches, matches


def test_storage_usage_intent_ranks_app_usage_above_storage_breakdown() -> None:
    """In-product-agent evidence: 'how much storage am I using, and what plan
    am I on?' only ever reached workspace.storage-breakdown -- a paginated
    per-item list with no total that paged through 300+ projects and never
    produced a number. workspace.app-usage carries the actual total
    (storage_used/current_storage_allowed/plan_storage_value/
    max_storage_allowed) and must rank first for a storage-usage query.
    """
    for query in ("storage used", "how much storage", "storage usage", "space used"):
        matches = [item["command_id"] for item in find_schemas(query)["matches"]]
        assert matches, f"no full match for {query!r}"
        assert matches[0] == "workspace.app-usage", f"{query!r} -> {matches}"


def test_per_dataset_storage_intent_reaches_storage_breakdown() -> None:
    """Live-eval evidence: goals asking which datasets/projects use the most
    storage (dataset details, dataset storage metrics, per-project storage
    usage) matched dataset.get, workflow.workspace-datasets and
    workspace.app-usage -- never workspace.storage-breakdown, the one
    command whose result is actually a per-dataset (and per-project) size
    breakdown. It must not regress the query above: those stay
    workspace.app-usage's own generic "total storage used" phrasing.
    """
    for query in (
        "which datasets use the most storage",
        "storage used by each dataset",
        "largest datasets by storage size",
        "per project storage breakdown",
    ):
        matches = [item["command_id"] for item in find_schemas(query)["matches"]]
        assert "workspace.storage-breakdown" in matches, f"{query!r} -> {matches}"


def test_independent_dataset_copy_intent_reaches_view_create() -> None:
    """Live-eval evidence (T1-T-28): 'keep this table as is, but give the West
    team their own copy they can change' -- the model tried 'copy or
    duplicate a dataset', 'duplicate dataset as independent copy', 'clone
    dataset without changing source view pipeline'; view.create (a new view
    on the same dataset is exactly that editable, source-preserving copy)
    never ranked for any of them.
    """
    for query in (
        "copy or duplicate a dataset",
        "duplicate dataset as independent copy",
        "clone dataset without changing source view pipeline",
    ):
        matches = [item["command_id"] for item in find_schemas(query)["matches"]]
        assert "view.create" in matches, f"{query!r} -> {matches}"


def test_support_family_ranks_below_any_non_support_match_and_is_labeled() -> None:
    matches = find_schemas("workspace user")["matches"]
    is_support = [m["command_id"].startswith("support.") for m in matches]
    assert any(is_support) and not all(is_support), "expected a mix of support and non-support"
    # Every support.* result must sit after every non-support result.
    assert is_support == sorted(is_support)
    assert all(m.get("operator_only") for m, support in zip(matches, is_support) if support)
    assert all("operator_only" not in m for m, support in zip(matches, is_support) if not support)


def test_brief_schema_keeps_nested_shape_for_non_scalar_fields() -> None:
    """Brief mode stripped every field's schema, even a nested object/array,
    leaving only a bare type name (e.g. 'DateDelta') to guess the shape of.
    Non-scalar fields must keep their schema; scalars still get stripped.
    """
    full = get_schema("view.transform.increment-date")
    assert full is not None
    brief = brief_schema(full)
    fields = {field["name"]: field for field in brief["accepted_fields"]}

    delta = fields["delta"]
    assert "schema" in delta
    assert set(delta["schema"]["properties"]) >= {"days", "weeks", "months", "years"}

    column = fields["column"]
    assert "schema" not in column


def test_math_intent_phrasings_rank_math_first() -> None:
    """Cold-agent recall gap: both phrasings took 3 searches to reach math.

    view.transform.math already supports a per-row 'condition' (a formula
    applied only where the condition holds, e.g. a value over a threshold),
    so the second query legitimately targets math, not just the first.
    """
    for query in (
        "calculate a new column using multiplication",
        "math conditional formula text if greater than threshold",
    ):
        matches = [item["command_id"] for item in find_schemas(query)["matches"]]
        assert matches, f"no full match for {query!r}"
        assert matches[0] == "view.transform.math", f"{query!r} -> {matches}"


def test_csv_export_contract_does_not_preserve_stale_permission_block() -> None:
    """Retained live evidence supersedes the old blanket export restriction."""
    schema = get_schema("view.export.csv")
    assert schema is not None
    assert "Live dataset permission is currently blocked" not in schema["preconditions"]


def test_ingestion_contract_preserves_supported_path_and_variant_boundaries() -> None:
    """Published discovery must not turn retained live evidence into a blanket block."""
    dataset_create = get_schema("dataset.create")
    file_upload = get_schema("file.upload")
    assert dataset_create is not None and file_upload is not None

    assert "BLOCKED[B06" not in dataset_create["preconditions"]
    assert "ds_creation_type=weburl" in dataset_create["preconditions"]
    assert dataset_create["async"] == "always_wait"
    assert (
        "variants beyond the documented path are not qualified" in dataset_create["preconditions"]
    )

    assert "IO-LIVE-PERMISSION" not in file_upload["preconditions"]
    assert "tenant- and scope-specific" in file_upload["preconditions"]
    # The contract states the measured boundaries instead of a blanket block.
    assert "Accepted extensions" in file_upload["preconditions"]
    assert "not json" in file_upload["preconditions"]
    assert "HTTP 413" in file_upload["preconditions"]
    assert "do not assume other upload variants are qualified" in file_upload["preconditions"]


def test_date_diff_documents_diffing_against_today() -> None:
    """date-diff's start/end only accept existing DATE columns; the server's
    SYSTEM_TIME operand (diff against the current execution time, e.g. 'days
    since order') is undocumented and only reachable via a raw task. The
    schema's preconditions must say so, with the exact recipe.
    """
    schema = get_schema("view.transform.date-diff")
    assert schema is not None
    restrictions = schema["preconditions"]
    assert "today" in restrictions.casefold()
    assert "view task add" in restrictions
    assert "__TIME__" in restrictions


def test_json_extract_documents_list_to_rows_item_and_index() -> None:
    """JSON_LIST_TO_ROWS gives one row per list element in an 'Item' column
    (plus 'Index'); an object element needs a second json-extract
    (json_type=OBJECT) on Item to become columns. An agent choosing between
    LIST and OBJECT must see this without reading the SDK source.
    """
    schema = get_schema("view.transform.json-extract")
    assert schema is not None
    restrictions = schema["preconditions"]
    assert "Item" in restrictions
    assert "Index" in restrictions
    assert "one row per" in restrictions.casefold()
    assert "second json-extract" in restrictions.casefold()


def test_automation_create_documents_the_email_csv_row_limit() -> None:
    """A scheduled email action (task send_an_alert, attachments.dataview_ids)
    sends each selected view as a CSV file. The 100,000-row cap (backend:
    _validate_attachment_row_count, EMAIL_CSV_ATTACHMENT_ROW_LIMIT) is on the
    COMBINED row count across all attached views, not per view; an agent
    must see the format and the real (combined) cap without reading the
    backend source.
    """
    schema = get_schema("automation.create")
    assert schema is not None
    restrictions = schema["preconditions"]
    assert "csv" in restrictions.casefold()
    assert "100,000" in restrictions
    assert "combined" in restrictions.casefold()
    assert "per view" not in restrictions.casefold()


def test_publish_db_and_powerbi_document_that_the_target_refreshes_on_rerun() -> None:
    """T1-O-08: an agent found both typed exports, then talked itself out of
    calling either one over an unstated worry about whether the destination
    stays live. Both become a persistent pipeline step (like `view export
    dataset`): the target refreshes automatically every time the source
    view's pipeline reruns, not just once at call time.
    """
    for command_id in ("view.export.publish-db", "view.export.powerbi"):
        schema = get_schema(command_id)
        assert schema is not None
        restrictions = schema["preconditions"]
        assert "refresh" in restrictions.casefold(), command_id
        assert "rerun" in restrictions.casefold() or "re-run" in restrictions.casefold(), command_id


def test_dataset_create_sdk_catalog_does_not_conflate_cli_waiting() -> None:
    """The SDK returns a job handle; the CLI handler owns its always-wait policy."""
    catalog = yaml.safe_load(
        (ROOT / "spec" / "manifests" / "sdk-catalog.source.yaml").read_text(encoding="utf-8")
    )
    record = next(
        item
        for item in catalog["sdk_methods"]
        if item["sdk_symbol"] == "mammoth.api.datasets.DatasetsAPI.create"
    )
    schema = get_schema("dataset.create")
    assert record["wait_policy"] == "not_async"
    assert "CLI command waits for the raw SDK job" in record["notes"]
    assert schema is not None and schema["async"] == "always_wait"


def test_schema_omits_fields_that_handlers_ignore_or_replace() -> None:
    skill = get_schema("skill.install")
    job = get_schema("job.get")
    assert skill is not None and job is not None
    skill_fields = {field["name"] for field in skill["accepted_fields"]}
    job_fields = {field["name"] for field in job["accepted_fields"]}
    assert {"home", "cwd", "timestamp"}.isdisjoint(skill_fields)
    assert "timeout" not in job_fields
    assert {"home", "cwd", "timestamp"}.isdisjoint(skill["input_schema"]["properties"])
    assert "timeout" not in job["input_schema"]["properties"]


def test_id_collection_schema_requires_positive_non_empty_ids() -> None:
    schema = get_schema("project.bulk-delete")
    assert schema is not None
    project_ids = schema["input_schema"]["properties"]["project_ids"]
    assert project_ids["minItems"] == 1
    assert project_ids["items"]["minimum"] == 1


def test_build_time_example_uses_explicit_operation_ids_not_generated_manifest(
    monkeypatch,
) -> None:
    """A clean manifest build cannot read the output it is in the middle of creating."""
    monkeypatch.setattr(
        "mammoth_cli.services.openapi_types.command_by_id",
        lambda _command_id: (_ for _ in ()).throw(AssertionError("manifest lookup")),
    )
    monkeypatch.setattr(
        "mammoth_cli.commands.schema.resolve_positionals",
        lambda _command_id: (_ for _ in ()).throw(AssertionError("manifest lookup")),
    )
    record = {
        "command_id": "dashboard.context.create",
        "command_path": "dashboard context create",
        "operation_ids": ["CreateContext"],
    }
    example = runnable_example(
        record,
        "mammoth.api.dashboards.DashboardsAPI.context_create",
        positionals_for(record["command_id"], None),
    )
    assert example is not None
    document = json.loads(shlex.split(example)[5])
    assert document == {"body": {"params": {"name": "Revenue report"}}}


def test_schema_get_names_secret_fields_and_routes_their_example_through_a_file() -> None:
    from mammoth_cli.output.normalize import normalize

    postgres = get_schema("view.export.postgres")
    csv = get_schema("view.export.csv")
    assert postgres is not None and csv is not None

    assert postgres["secret_fields"] == ["password"]
    assert csv["secret_fields"] == []
    # The list names protected fields; it must survive output redaction so an
    # agent can see which commands need ``--input FILE``.
    assert normalize({"secret_fields": ["password"]}) == {"secret_fields": ["password"]}
    assert "/private/path/request.json" in postgres["agent_example"]
    assert "password" not in postgres["agent_example"]


@pytest.mark.parametrize(
    "query",
    [
        "power bi file",
        "tableau workbook",
        "pbix",
        "twbx",
        "open this board in power bi",
    ],
)
def test_dashboard_bi_file_intent_ranks_bi_export_first(query: str) -> None:
    """The in-product agent cannot run 'give me this board as a Power BI
    file' unless schema find surfaces the dashboard-to-file export commands
    ahead of the unrelated view.export.powerbi/.tableau (which publish a
    live ODBC connection for a dataview, not a downloadable file for a
    dashboard) and ahead of dashboard.assess-pbix/.import-workbook (the
    opposite, import direction).
    """
    matches = [item["command_id"] for item in find_schemas(query)["matches"]]
    assert matches, f"no full match for {query!r}"
    assert matches[0] in ("dashboard.bi-export", "dashboard.bi-preflight"), (query, matches)


@pytest.mark.parametrize(
    "query",
    [
        "bring my power bi report in",
        "import tableau workbook",
        "move my old dashboards over",
    ],
)
def test_migrate_workbook_intent_ranks_import_workbook_first(query: str) -> None:
    """The opposite direction of the BI-file export pair: bringing an
    existing Power BI/Tableau workbook INTO Mammoth is dashboard.import-
    workbook, not dashboard.bi-export/.bi-preflight (which go the other way).
    """
    result = find_schemas(query)
    top = result["matches"] or result.get("suggestions", [])
    assert top, f"no match or suggestion for {query!r}"
    assert top[0]["command_id"] == "dashboard.import-workbook", (query, top)


def test_find_with_no_full_match_inlines_how_to_call_the_top_suggestions() -> None:
    """A long goal rarely matches every word; the top suggestions still carry the
    input fields and an example, so one find is enough to act (no schema get)."""
    result = find_schemas("aggregate rows by date year month and count by result")
    assert result["matches"] == []
    top = result["suggestions"][:3]
    assert "view.data.explore" in [entry["command_id"] for entry in top]
    for entry in top:
        assert "accepted_fields" in entry
        assert "agent_example" in entry
    assert all("accepted_fields" not in entry for entry in result["suggestions"][3:])


@pytest.mark.parametrize(
    "query",
    [
        "aggregate view data grouped by date and category",
        "aggregate view data group by date and result",
        "view data aggregate by month",
    ],
)
def test_find_ranks_a_command_named_in_the_query_first(query: str) -> None:
    """A query that spells out a command's path (in any order) is asking for that
    command, whatever other goal words it carries (koyal trending traces)."""
    result = find_schemas(query)
    assert result["matches"], result.get("suggestions")
    assert result["matches"][0]["command_id"] == "view.data.aggregate"
    assert "accepted_fields" in result["matches"][0]


def test_connector_connection_credentials_are_secret_fields_sent_through_a_file() -> None:
    """``config`` on create and ``credentials`` on update ARE the connection's
    secret, so their examples must not inline it on the command line."""
    create = get_schema("connector.connection.create")
    update = get_schema("connector.connection.update")
    assert create is not None and update is not None

    assert create["secret_fields"] == ["config"]
    assert update["secret_fields"] == ["credentials"]
    for schema in (create, update):
        assert schema["agent_example"].endswith("--input /private/path/request.json")


def test_a_find_points_into_the_families_it_matched() -> None:
    """A keyword search over hundreds of commands finds one way to do a thing;
    the family it lives in holds the siblings (other export targets, other
    joins). Every find names those families and how to list them, so the agent
    can drill down instead of guessing more keywords."""
    result = find_schemas("export view csv")

    families = result["browse"]["families"]
    assert families
    assert families == list(dict.fromkeys(m["command_path"].split()[0] for m in result["matches"]))
    assert result["browse"]["next"].startswith("mammoth schema list FAMILY")


def test_a_find_with_no_match_still_points_into_families() -> None:
    result = find_schemas("zzqx frobnicate")

    assert "browse" in result
    assert "mammoth schema list" in result["browse"]["next"]
