"""Schema discovery generated from the reviewed command manifests.

Returns each command's request/result models, examples, policies, and test ids
so an agent can construct a valid invocation without reading source. The
accepted request fields (name, type, enum values, default, required) and the
positional arguments (name, type, required, metavar) are derived from the
command's backing SDK signature (see :mod:`mammoth_cli.services.argspec` and
:mod:`mammoth_cli.services.positionals`), so discovery reports the real,
always-current shape rather than the manifest's placeholder empty lists. A
synthesized, fully runnable example command line is included for every command
with a resolvable signature, so an agent never has to guess how a positional
and an ``--input`` document combine.
"""

from __future__ import annotations

import json
import re
import shlex
from collections import defaultdict
from functools import cache
from typing import Any, cast

from mammoth_cli.manifest.loader import command_by_id, load_commands, load_operations
from mammoth_cli.output.normalize import trusted_json_schema
from mammoth_cli.services.argspec import FieldSpec
from mammoth_cli.services.command_contract import LOCAL_COMMANDS, resolve_command_contract
from mammoth_cli.services.input_fields import (
    example_input_hints,
    excluded_input_fields,
    handler_owned_fields,
)
from mammoth_cli.services.openapi_types import openapi_body_schema_for, sample_from_schema
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals
from mammoth_cli.services.type_system import is_opaque_mapping, json_schema, sample_value

# Agent examples carry no ``--output json --no-input``: a piped run already
# gets machine JSON and never prompts, and ``MAMMOTH_OUTPUT``/``MAMMOTH_NO_INPUT``
# cover a session that is not piped.
_OUTPUT_JSON_NO_INPUT: tuple[str, ...] = ()
# A command whose request carries a secret never gets an inline JSON example:
# the published example points at a protected owner-only file instead, so no
# generated or copied command line ever puts a credential in argv.
_PROTECTED_INPUT_PATH = "/private/path/request.json"
# Commands whose useful example the SDK signature cannot express: a distinct
# second id, an optional-but-central input field, or two views to compare.
_FIXED_EXAMPLES: dict[str, tuple[tuple[str, ...], dict[str, Any]]] = {
    "project.check": (("123", "456"), {}),
    "view.data.profile": (("123",), {"target": "Churn"}),
    "workflow.canvas": (
        ("12",),
        {
            "canvas_state": {
                "proposed_changes": [
                    {
                        "op": "add_view",
                        "dataset_id": 415,
                        "name": "Urgent tickets",
                        "ref": "urgent",
                    },
                    {
                        "op": "send_to_new_dataset",
                        "dataset_id": 415,
                        "view_ref": "urgent",
                        "name": "Urgent tickets by team",
                    },
                ]
            }
        },
    ),
    "view.data.compare": (
        ("111", "222"),
        {
            "group_by": ["Campaign"],
            "aggregations": [{"column": "Spend", "function": "SUM", "as_name": "Spend"}],
        },
    ),
}
_OPAQUE_EXPERT_COMMANDS = frozenset({"view.task.add", "view.task.preview", "view.task.update"})
_TYPED_TRANSFORM_ALTERNATIVES = [
    "view.transform.filter",
    "view.transform.join",
    "view.transform.math",
]

# Human intent often uses the resource's familiar format or outcome rather
# than a literal command token.  These small, stable hints supplement (never
# replace) manifest and OpenAPI text during compact discovery.
_GROUP_DISCOVERY_PURPOSES = {
    "dataset": "data import tables CSV spreadsheet",
    "file": "source file storage",
    "view": "transform query clean analyze data pipeline",
    "dashboard": "build visualize share chart charts report analytics",
    "workflow": "automate pipeline orchestration",
}

_COMMAND_DISCOVERY_PURPOSES = {
    "view.update": "rename change name to a new name title relabel",
    "file.upload": (
        "upload import CSV spreadsheet XLSX source data append add rows union stack "
        "a file into an existing dataset excel workbook tabs sheets drop in"
    ),
    "file.upload-folder": "upload source-data directory folder",
    "view.export.csv": "export download local CSV file artifact",
    "view.export.dataset": (
        "send copy branch out create save the result rows into a new project from an "
        "existing append appending union stack monthly rows across datasets views"
    ),
    # One entry per typed export destination, in the way users name the
    # destination rather than Mammoth's route spelling (which a two-word
    # phrase like "power bi" may not literally contain -- see the adjacent
    # term-pair match in find_schemas for "powerbi"/"bigquery"/etc).
    "view.export.azure-blob": "azure blob storage container",
    "view.export.bigquery": "big query bigquery google cloud database table",
    "view.export.elasticsearch": "elasticsearch elastic search index",
    "view.export.email": "email send mail attachment",
    "view.export.ftp": "ftp file transfer protocol server",
    "view.export.managed-s3": "s3 amazon aws bucket managed storage",
    "view.export.mssql": "sql server mssql microsoft database",
    "view.export.mysql": "mysql database",
    "view.export.onedrive": "one drive onedrive microsoft cloud storage",
    "view.export.postgres": "postgres postgresql database",
    "view.export.powerbi": "power bi powerbi microsoft dashboard workspace",
    "view.export.publish-db": (
        "publish database live connection odbc bi tool reads table point straight at always latest"
    ),
    "view.export.publish-db-update": "publish database update refresh live connection",
    "view.export.redshift": "redshift amazon aws database warehouse",
    "view.export.rest": "webhook http endpoint api push rest",
    "view.export.sftp": "sftp secure file transfer server",
    "view.export.sharepoint": "share point sharepoint microsoft",
    "view.export.tableau": "tableau server dashboard",
    # "Run"/"execute"/"apply"/"refresh" the pipeline is ambiguous between
    # re-running its tasks and applying a pending draft; both need to surface.
    "view.pipeline.rerun": (
        "run execute rerun re-run refresh recompute apply pipeline tasks "
        "from a point in the task sequence"
    ),
    "view.draft.submit": "apply submit run execute a pending draft changes",
    "webhook.update": "webhook http endpoint api update",
    "webhook.get": "webhook http endpoint api get",
    "webhook.list": "webhook http endpoint api list",
    "webhook.delete": "webhook http endpoint api delete",
    "webhook.send": "webhook http endpoint api push send",
    "webhook.send-get": "webhook http endpoint api pull send get",
    # "What did I ask you about earlier this week?" is a lookup over past
    # agent conversations. Live-eval evidence: `schema find` on that phrasing
    # never matched `agent.session.list`/`agent.session.messages` because
    # neither command's own text says "conversation", "chat", "history", or
    # "asked" -- and the unrelated per-project `connector.ai.session.*`
    # family, whose OpenAPI summary literally says "chat session", outranked
    # them. These two ARE the past-conversation lookup: list the sessions,
    # then read one's messages.
    # "Pick up where we left off last time" / "continue where I left off" /
    # "resume my previous conversation" is the same past-conversation lookup
    # under different wording -- the model instead searched "recent project
    # activity" and "activity list", since neither command said "left off",
    # "last time", "resume", "pick up", or "continue".
    "agent.session.list": (
        "chat conversation conversations history past previous asked earlier week "
        "messages sessions where left off last time resume pick up continue"
    ),
    "agent.session.messages": (
        "chat conversation conversations history past previous asked earlier week read "
        "where left off last time resume pick up continue"
    ),
    "workspace.user.add": (
        "invite add member teammate email role editor viewer admin assign permission access"
    ),
    # Client apps ARE the product's API keys: the key + secret credentials a
    # script or integration uses to call Mammoth. Live-eval evidence: "list
    # active API keys" only ever reached external-key.list (LLM provider
    # keys), never this command, because nothing in its text said "API key".
    "client-app.list": (
        "api keys api key secret credentials workspace active script integration list"
    ),
    # "How much storage am I using, and what plan am I on?" only ever reached
    # workspace.storage-breakdown -- a paginated per-item list with no total
    # that pages through every project before giving up. This command's own
    # text says neither "storage" nor "usage"; it is the one that carries the
    # actual total (storage_used/current_storage_allowed/plan_storage_value/
    # max_storage_allowed).
    "workspace.app-usage": (
        "storage usage used space how much plan current allowed total quota limit"
    ),
    # "Which datasets use the most storage" / "storage used by each dataset"
    # / "per-project storage breakdown" only ever reached dataset.get,
    # workflow.workspace-datasets or workspace.app-usage (the total, not a
    # breakdown) -- never this command, the one whose result actually is a
    # per-dataset (and per-project) size list (dataset_id, dataset_name,
    # project_id, dataset_size, total_size, views). Deliberately omits
    # "storage" (already an id/path token here, unlike app-usage) so a bare
    # "storage used" query keeps ranking app-usage's own total first.
    "workspace.storage-breakdown": (
        "size used use per dataset datasets project projects largest biggest most which top"
    ),
    # "Give me this board as a Power BI file" / "open this in Tableau" is the
    # dashboard-to-BI-file export pair, not `view.export.powerbi`/`.tableau`
    # (those publish a live ODBC connection for a dataview, not a downloadable
    # file for a dashboard). Both destinations' vocabulary lives on both
    # commands: the dialog answers "what will I get" the same way for either
    # tool (see PowerBiPreflightResponse/TableauPreflightResponse), and the
    # export downloads whichever the caller names via input `target`.
    # "publish a dashboard OR ITS UNDERLYING VIEW to Power BI" (T1-D-22) hedges
    # with "view" even though the export is dashboard-only; without "view" in
    # this text the strict all-terms gate drops these two and the unrelated
    # view.export.powerbi (a raw ODBC connector, literally named "view") wins.
    "dashboard.bi-preflight": (
        "power bi powerbi pbix pbip tableau twb twbx workbook file board view open this "
        "dashboard board in power bi desktop or tableau desktop preview dry run what would "
        "convert figures rows before downloading export"
    ),
    "dashboard.bi-export": (
        "power bi powerbi pbix pbip tableau twb twbx workbook file board view open this "
        "dashboard board in power bi desktop or tableau desktop download export save project "
        "convert"
    ),
    # "Bring my old Power BI report in" / "move my dashboards over" is the
    # workbook-to-Mammoth-dataset import, the opposite direction of
    # `dashboard.bi-export`. The command id's own tokens ("import",
    # "workbook") already cover half of this -- "workbook" is deliberately
    # NOT repeated below: it would double-score (command-id token AND purpose
    # match) and outrank `dashboard.bi-export`/`.bi-preflight` on the bare
    # "tableau workbook" phrasing those two must win instead. Only "tableau"
    # (its own text says neither tool's name) and the migration verbs are new.
    "dashboard.import-workbook": (
        "bring in migrate move transfer switch old existing dashboards dashboard over power "
        "bi report tableau file upload"
    ),
    # One entry per ``view transform`` command, in the words a user states a
    # goal in rather than Mammoth's own task names.  This is the CLI's version
    # of the web app's Transform menu; keep every transform listed.
    "view.transform.add-column": "add column new empty blank column",
    "view.transform.add-sql": "sql query select statement replaces every column",
    "view.transform.ai": (
        "ai llm prompt generative classify categorize categorise sentiment enrich "
        "summarize summarise rows into a new column"
    ),
    "view.transform.bulk-replace": (
        "find replace strip characters text values mapping standardize standardise "
        "normalize normalise variants many to one"
    ),
    "view.transform.combine-columns": (
        "combine concatenate concat columns values into one column separator"
    ),
    "view.transform.convert-type": (
        "convert type cast numeric number text date column parse to number to date"
    ),
    "view.transform.copy-columns": "copy duplicate column into a new column",
    "view.transform.crosstab": (
        "crosstab cross tab pivot table matrix rows by columns summary into a new dataset"
    ),
    "view.transform.date-diff": "date dates difference days between two date columns age duration",
    "view.transform.delete-columns": "delete drop remove columns",
    "view.transform.discard-duplicates": (
        "duplicate duplicates dedup dedupe deduplicate remove repeated rows unique distinct "
        # "order"/"number" are kept as generic identifying-column vocabulary
        # ("dedupe by an order/number/key"), not the specific business noun
        # "order id" -- "order" also can't be dropped as a data word since
        # view.transform.sort's own purpose text already uses it (sort
        # order), so any query pairing "order" with dedupe words needs it
        # covered here to reach a full match.
        "by order number key column"
    ),
    "view.transform.extract-date": (
        "extract date part year month day hour minute second week quarter weekday "
        "month_text into a new column"
    ),
    "view.transform.fill-missing": (
        "fill missing null empty blank blanks impute carry forward fill down values"
    ),
    "view.transform.filter": (
        "filter rows keep drop exclude remove delete rows where condition subset "
        "bind bound binding parameter"
    ),
    "view.transform.generate-sql": "generate write sql query from natural language intent question",
    "view.transform.increment-date": "add subtract days months years to a date column shift",
    "view.transform.join": (
        "join blend merge combine enrich match matching key keys rows add columns from "
        "another second view views dataset datasets table tables vlookup"
    ),
    "view.transform.json-extract": (
        "json extract parse nested fields keys into columns list rows item index "
        "one row per element explode array"
    ),
    "view.transform.limit-rows": "limit top bottom first last n rows head",
    "view.transform.lookup": (
        "lookup look up vlookup reference table map code to name enrich one value "
        "from another view dataset"
    ),
    "view.transform.math": (
        "math arithmetic multiply multiplication divide add subtract formula "
        "expression amount calculate compute ratio percentage round new column "
        "conditional threshold greater than if text times"
    ),
    "view.transform.pivot": (
        "pivot group by aggregate aggregation sum count average summary summarize "
        "summarise per region total"
    ),
    "view.transform.rename-columns": (
        "rename column columns header headers relabel change column name names title"
    ),
    "view.transform.replace": "find replace substitute text value in columns",
    "view.transform.set-values": (
        "set values assign overwrite blank empty default where condition label "
        "category bucket flag if then conditional add a column with a constant value"
    ),
    "view.transform.small-large": "nth smallest largest value across columns",
    "view.transform.sort": (
        "sort sorting order rows by column ascending descending asc desc arrange "
        "highest lowest newest oldest latest earliest date dates alphabetical"
    ),
    "view.transform.split": "split column by delimiter separator into columns",
    "view.transform.substring": "substring left right characters regex pattern extract part text",
    "view.transform.text": (
        "text case upper uppercase lower lowercase title trim whitespace normalise normalize"
    ),
    "view.transform.unnest": (
        "unnest unpivot melt wide to long columns into label value rows reshape"
    ),
    "view.transform.window": (
        "window rank row number running total cumulative sum moving average lag lead "
        "previous next row partition"
    ),
    # The web app's column Explore cards: what is trending, how a column is
    # spread, its top values, a count over time.
    "view.data.explore": (
        "explore trend trends trending over time per day week month quarter year by date "
        "distribution spread histogram top most common frequent values breakdown share "
        "percentage profile period year quarter month date range coverage figure "
        "cumulative"
    ),
    # "Give the West team their own copy they can change" / "duplicate this
    # dataset as an independent copy" / "clone it without changing the
    # source pipeline" -- a new view on the same dataset IS that editable
    # copy (its own pipeline, the source view untouched) but none of these
    # phrasings ever reached it; the query's own incidental words (schema
    # find is an AND-term search) needed saying explicitly.
    "view.create": (
        "start a new one from an existing dataset, duplicate copy clone "
        "independent without changing the source pipeline"
    ),
    "dataset.list": "list every dataset in a project workspace",
    # "month"/"week" are kept as generic calendar-grouping vocabulary (a
    # group-by dimension any dataset can have), not a specific business
    # value -- and neither can be dropped as a data word anyway, since
    # view.data.explore's own purpose text already uses both for its trend
    # feature.
    "view.data.aggregate": (
        "group and sum totals by month week without changing the pipeline "
        "sum total figure answer a question, read only"
    ),
    # Goals stated as "what is in this data" / "why do customers churn": one
    # whole-view profile answers both, so the phrasing must reach it.
    "view.data.profile": (
        "profile explore what is in this data understand a dataset every column blanks missing "
        "empty nulls distinct unique duplicates dirty inconsistent categories spelling variants "
        "check look at overview summary statistics churn drivers drive driving feature "
        "importance correlation which columns predict affect influence the target outcome"
    ),
    # Goals users state in their own words, one entry per command the agent's
    # system prompt used to spell out by hand.
    "dashboard.suggestion.list": "ideas suggest suggestions what to show put on a board chart",
    "dashboard.analytics": "who viewed seen opened views visitors usage of a board",
    "dashboard.share": "share make live publish board for the team link access",
    # "Import a table from SQL Server / MySQL / Postgres into a dataset" is a
    # connector flow -- list connectors, create a connection, then a ds-config
    # (a table or query pulled in as a new dataset) -- but none of these
    # commands said "database", "table", "SQL Server" or "import", so every
    # phrasing missed them and only the unrelated view.export.* commands
    # (which push data OUT to a database) matched.
    "connector.list": (
        "connectors available sources database SQL Server MSSQL MySQL Postgres Oracle "
        "connect import pull load table into dataset"
    ),
    "connector.get": (
        "connector database SQL Server MSSQL MySQL Postgres connection fields host port "
        "username password required to connect import table dataset"
    ),
    "connector.connection.list": (
        "which outside external sources connected connections list database SQL Server "
        "MSSQL MySQL Postgres connector already connected import table dataset"
    ),
    "connector.connection.get": (
        "connection database SQL Server MSSQL MySQL Postgres connector connected "
        "import table dataset"
    ),
    "connector.connection.create": (
        "connect a database such as SQL Server MSSQL MySQL Postgres Oracle host username "
        "password new connection connector to import a table into a dataset"
    ),
    "connector.ds-config.create": (
        "import pull load read retrieve a table or SQL query from a connected database such "
        "as SQL Server MSSQL MySQL Postgres connector connection as a new dataset rows data"
    ),
    "connector.ds-config.list": (
        "datasets imported from a connected database SQL Server MSSQL MySQL Postgres "
        "connector table query import configurations"
    ),
    "connector.query.generate": (
        "write SQL from plain words for a connected database SQL Server MSSQL MySQL "
        "Postgres connector import rows query"
    ),
    "project.pending-changes": (
        "source changes new rows not taken in yet pending updates waiting to apply"
    ),
    # "I pasted a link to a file / dataset / view -- what is wrong with it?" (zulip
    # Mammoth Agents, ws 247): the agent had no way to turn the app address into
    # ids, and the unstructured-rows read said "broken" where users say "unstructured".
    "link": (
        "link url pasted address app page open file dataset view folder project "
        "workspace ids selected resource parse"
    ),
    "dataset.broken-rows.list": (
        "unstructured skipped ragged rows lines unparsed mismatched columns monitor "
        "needs review file upload bad rows"
    ),
    "dataset.broken-rows.resolve": (
        "fix unstructured skipped ragged lines discard correct resolve mismatched "
        "columns review monitor needs review upload"
    ),
    "project.needs-attention": (
        "monitor needs attention error failing pipeline views delete datasets behind list "
        "unstructured pending review"
    ),
    "project.resource-status": "stuck stale failing broken error status anything wrong health",
    "dashboard.embed.usage.summary": (
        "embedded sites how many websites pages embed my boards library all dashboards origins"
    ),
    "dashboard.format-preview": (
        "switch format style what would change lose carry over preview dry run report slides"
    ),
    "workspace.home": (
        "home screen health issues needs attention overview usage snapshot suggestions"
    ),
    "browse.resources": (
        "page through project resources cursor next page has more folder children v2 listing"
    ),
    "browse.resource": "open one resource by type and id properties of a dataset view folder",
    "browse.resources.bulk": "fetch many resources by type and id in one request batch lookup",
    "agent.turn.cancel": "stop the agent now cancel this turn halt what the assistant is doing",
    "dashboard.swap-fit": "which dataset fits this dashboard before swapping data score candidates",
    "dashboard.audience.get": "who opened my dashboard readers visitors audience over time",
    "dashboard.audience.summary": "how many people opened each dashboard in the library",
    "dashboard.audience.digest.get": "weekly audience email setting for a dashboard get",
    "dashboard.audience.digest.set": "turn the weekly audience email on or off for a dashboard",
    "dashboard.columns": "columns of the dashboard source data profile samples ranges data panel",
    "dashboard.context.review": "preview what the context change would do to the dashboard dry run",
    "dashboard.context.apply": "apply the reviewed context change to the dashboard",
    "dashboard.qa.insights": "what questions viewers asked on the dashboard grouped unanswered",
    "view.impact": "what breaks if I delete this dataview or a task dependents impact",
    "browse.ancestors": "folder path breadcrumb where does this folder live parent folders chain",
    "browse.search": (
        "find search a dataset view folder by name across all projects whole workspace global"
    ),
    "billing.stripe.resume": (
        "keep my plan cancel scheduled downgrade undo cancellation stay on paid plan resume"
    ),
    "billing.stripe.recheck-limits": (
        "over limit locked blocked after deleting items recheck plan limits clear the lock"
    ),
    "billing.stripe.storage.set": "buy more storage change purchased storage gb allocation",
    "dashboard.template.thumbnail.get": "template picture card image thumbnail download",
    "dashboard.template.thumbnail.set": "upload replace template picture card image thumbnail",
    "dashboard.template.thumbnail.clear": "remove delete template picture card image thumbnail",
    "dashboard.gallery.list": "public template gallery curated templates catalog examples browse",
    "dashboard.gallery.get": "one public gallery template card by slug",
    "support.plan.unarchive": "platform admin restore an archived subscription plan",
    "support.plan.storage-option.list": "platform admin plan storage sizes prices options",
    "support.plan.storage-option.create": "platform admin add a storage size price to a plan",
    "support.plan.storage-option.update": "platform admin reprice resize a plan storage option",
    "support.plan.storage-option.archive": "platform admin retire a plan storage option",
    "support.template.list": "platform admin curated template catalog worklist drafts faults",
    "support.template.edit": "platform admin retag rename reorder curated template filing",
    "support.template.data-preview": "platform admin curated template sample rows",
    "support.template.canvas": "platform admin curated template draft canvas review",
    "support.template.publish": "platform admin take curated template live in gallery",
    "support.template.unpublish": "platform admin take curated template down back to draft",
    "support.template.retire": "platform admin retire curated template stop offering",
    "support.template.inspect": "platform admin read template bundle zip before import",
    "support.template.import": "platform admin import template bundle zip curated draft",
    "support.template.thumbnail.set": "platform admin upload curated template picture",
    "support.template.thumbnail.clear": "platform admin remove curated template picture",
    "support.template.discard": "platform admin undo template import discard curated draft",
    "support.template.snapshots": "platform admin stored datasets behind curated templates",
    "support.template.audit": "platform admin audit curated template catalog gates faults",
    "support.template.export": "platform admin download curated template bundle zip",
    "support.template.export-dashboard": "platform admin download a board as template bundle zip",
    "connector.ai.chat": (
        "connect our own internal custom api build a connector for an unsupported source"
    ),
    "file.set-password": "locked password protected file pdf excel unlock",
    "project.sample-flow": "sample example demo starter data dataset try start from",
    "webhook.create": (
        "webhook http endpoint api push create data pushed in sent from another system receive "
        "url app post posts events rows straight in"
    ),
    "dataset.create-from-pdf": "pdf table document extract get the table out of into a dataset",
    # "import data from a public URL or JSON API into a dataset" / "fetch or
    # retrieve JSON from a public URL" (T1-I-16) never matched dataset.create
    # (ds_creation_type=weburl) -- the capability exists and works once found,
    # it just had no discovery-purpose text at all.
    "dataset.create": (
        "url web link fetch retrieve pull import public website endpoint api json data weburl"
    ),
    "dashboard.v3.generate": (
        "create build make new generate dashboard board report from a view description "
        "intent sentence ai combined showing"
    ),
    "dashboard.chat.edit": (
        "add change edit update chart charts kpi to an existing dashboard board "
        "by description sentence ai show instead"
    ),
    # "I messed up the board, put it back to how it was before" (T1-D-09) --
    # this is the version list dashboard.canvas.restore's target_sequence
    # comes from (revisions[]: sequence, updated_at, updated_by_name), but
    # nothing in its own path/purpose said undo/revert/before.
    "dashboard.chat.history": (
        "undo revert put back previous version before restore history versions saved "
        "last change board"
    ),
    "dashboard.pdf.export": "pdf of a board dashboard download print meeting export",
    # "single dashboard per-user or row-level region security" (T1-D-03) --
    # none of the dashboard.rls.* commands had any discovery-purpose text.
    "dashboard.rls.assignment.list": (
        "row row-level level security per user per-user per manager per-manager restrict "
        "each viewer to their own rows region"
    ),
    # "publish dashboard" / "make it live" (T1-D-15) -- dashboard.action is the
    # publish step dashboard.share depends on (fails with 4DASH010 otherwise),
    # but it had no discovery-purpose text at all.
    "dashboard.action": "publish make live go live unpublish share delete-source",
    # "list browse available dashboard templates styles; apply template to
    # current dashboard" (T1-D-12) returned 0 matches -- dashboard.template.*
    # had no discovery-purpose text (and the query's plural "templates" never
    # matches the family's singular path token "template").
    "dashboard.template.list": (
        "ready-made pre-built layout gallery browse choose templates styles available"
    ),
    "dashboard.template.apply": "apply a ready-made template layout to this board",
    "view.checkpoint.create": (
        "stop halt pause pipeline alert notify flag when if row rows match matches a rule "
        "condition checkpoint value changes"
    ),
    "view.data-check.create": "data quality check rule validate rows match condition flag",
    "view.derivative.create": "metric kpi number single value to check track daily monitor",
    "view.draft.auto-run": (
        "stop prevent re-running rerun automatically when source changes auto run enable disable"
    ),
    "data-app.create": (
        "page portal form others drop upload a file cleaned the same way self service"
    ),
    # "does automation support pdf" -- what an automation reads, writes, triggers on
    # and accepts is answered by the server, not by memory.
    "automation.capabilities": (
        "automation automations support supports supported pdf csv format formats file types "
        "can do what trigger triggers action actions task tasks option options capabilities"
    ),
    "automation.create": (
        "schedule scheduled recurring repeat refresh rerun run every day daily week weekly "
        "hour hourly month monthly automatically trigger alert email a dataset pipeline "
        "retention purge old data send an emailed file attachment view views csv new folder "
        "arrives lands dropped"
    ),
    # "current subscription plan tier for workspace; billing plan and storage
    # allowance" (T1-W-06) never matched -- "plan and storage allowance"/
    # "subscription tier" phrasing had no discovery-purpose text on either
    # billing command. Deliberately no "much"/generic "how much" wording here:
    # that would also fully-match the bare "how much storage" query and tie
    # workspace.app-usage on score (alphabetical tie-break would then wrongly
    # rank this ahead of it -- see storage_usage_intent guard test).
    "billing.chargebee-plan": (
        "current subscription tier plan storage allowance space included for workspace"
    ),
    "billing.subscription.update": "upgrade downgrade bigger plan change subscription tier",
    "billing.invoice.list": "past bills billed billing history invoices payments receipts so far",
    "project.memory.add": (
        "remember save preference prefer prefers always from now on note for next time "
        "amounts currency format style"
    ),
    # A rule about what a board's data means ("Returned orders are refunds") is
    # the board's own context, not the user's preference.
    "dashboard.context.create": (
        "remember for this board dashboard rule meaning definition counts treat as business context"
    ),
    "project.memory.list": "remembered saved preferences what do you remember memory",
    "project.memory.remove": "forget remove delete saved preference memory",
    # A workflow's shape can be proposed for the user to review and Save on the
    # canvas; neither this nor naming a workflow was findable from the way users
    # ask (Workflow Zoo QA 10-02: "rename workflow" found column renames).
    "workflow.canvas": (
        "propose suggest sketch draft plan review approve save structural changes "
        "to a workflow pipeline shape on the canvas new views datasets send to join "
        "export for the user to review"
    ),
    "workflow.update": "rename name describe a workflow pipeline purpose notes summary",
    "workflow.create": "name an unnamed workflow pipeline from the root dataset new workflow",
}

# A compact string scope is retained for existing discovery consumers.  These
# reviewed exceptions add the exact binding facts an agent needs for the
# sensitive operations repaired in this release; do not infer a project parent
# merely from a command-family name.
_SCOPE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "project.user.update": {
        "kind": "project",
        "required_context": ["project_id"],
        "target_fields": ["user_id", "invite_id"],
        "target_rule": "exactly one target field is required by the backend contract",
    },
    "data-app.share": {
        "kind": "workspace",
        "required_context": ["workspace_id"],
        "target_fields": ["data_app_id"],
        "target_rule": "data_app_id is a required positional",
    },
    "view.exportable-config.apply": {
        "kind": "project",
        "required_context": ["project_id"],
        "target_fields": ["view_id", "dataset_id"],
        "target_rule": "view_id is required; dataset_id may be supplied or resolved from the view",
    },
}

_MAX_FIND_RESULTS = 20
# View transform/task commands add a step to the GIVEN view. An agent asked for
# a NEW dataset must know that before calling, so the statement is carried by
# every such command's contract (schema get ``preconditions``, find, --help).
_IN_PLACE_PREFIXES = ("view.transform.", "view.task.")
IN_PLACE_RECIPE = (
    "EDITS THE GIVEN VIEW IN PLACE: this adds a step to the view and changes that view "
    "and its dataset's output. To make a NEW dataset and leave the source untouched: "
    "`mammoth view create SOURCE_DATASET_ID` (working view), do the steps on that working "
    'view, then `mammoth view export dataset WORKING_VIEW_ID --input \'{"dataset_name": "..."}\'`.'
)
_IN_PLACE_KEYWORDS = (
    "new dataset create make in place edits given view working view source untouched"
)


def edits_view_in_place(record: dict[str, Any]) -> bool:
    """True for a view transform/task command that changes an existing view."""
    return bool(record.get("edits_target")) and str(record.get("command_id", "")).startswith(
        _IN_PLACE_PREFIXES
    )


# Outranks any word-overlap score: a command named by its full path comes first.
_NAMED_COMMAND_BOOST = 10_000
# Bag-of-words scoring cannot tell "create a NEW VIEW from an existing
# DATASET" (view.create) apart from "create a DATASET from an existing
# VIEW" (view.export.dataset): the two goals share the exact same word set,
# and only word order says which resource is being made and which already
# exists. No purpose text or synonym can encode that; this pair of small
# adjacency checks is the intentionally scoped exception. Extend the two
# dicts, never the regex, if another goal collides the same way.
_NEW_OBJECT_HINTS: dict[str, str] = {
    "view.create": "view",
    "view.export.dataset": "dataset",
}
_EXISTING_OBJECT_HINTS: dict[str, str] = {
    "view.create": "dataset",
    "view.export.dataset": "view",
}
_OBJECT_ADJACENCY_BOOST = 150
_MAX_FIND_LIMIT = 100
# How many of a find's top matches carry inline accepted_fields/agent_example.
# 35% of all eval tool calls were command discovery (schema find -> schema
# get) because find's compact entry gave a command_id but not what to pass
# it; inlining the top few lets an agent act without a second round trip in
# the common case where one of them is right. Bounded to a few commands so a
# broad query never balloons the result (the tool result goes into the
# model's context).
_INLINE_DETAIL_COUNT = 3

# Search is intentionally a small, deterministic intent matcher rather than a
# fuzzy/remote search service.  The aliases describe language users commonly
# use for a command; they do not add capabilities to the catalog.  Keeping the
# map here also makes a cold process produce the same ordering as a warm one.
_DISCOVERY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "show": ("list", "get", "browse", "display", "view"),
    "display": ("show", "list", "get", "view"),
    "visualize": ("dashboard", "chart", "analytics"),
    "spreadsheet": ("csv", "xlsx", "excel", "file", "upload"),
    "excel": ("spreadsheet", "xlsx", "file"),
    "csv": ("spreadsheet", "file", "upload"),
    "local": ("file", "download", "csv", "artifact"),
    "download": ("export", "file", "csv", "artifact", "local"),
    # "combine" alone is ambiguous between joining on a key and appending
    # rows; kept a weak alias match (not a literal word) here so a bare
    # "combine datasets" still favors join's own literal "combine" purpose
    # text, while "combine ... by appending rows" still resolves to the
    # export -- its own literal "append"/"union"/"stack" carry that case.
    "combine": ("append", "union", "stack", "merge"),
    # "publish" a dataset almost always means one of the typed exports
    # (Power BI, a live DB connection, a webhook, ...); every export
    # command's path literally contains "export", so this one alias covers
    # any "publish data to X" phrasing without a per-destination entry.
    "publish": ("export",),
    "column": ("columns", "field", "fields", "schema"),
    "columns": ("column", "field", "fields", "schema"),
    "display-name": ("name", "column", "columns", "field", "fields", "schema"),
    "language": ("name", "column", "columns", "field", "fields", "schema", "text"),
    "field": ("column", "columns", "fields"),
    "fields": ("column", "columns", "field"),
    "clean": ("transform", "replace", "remove", "edit"),
    "edit": ("transform", "update", "replace", "change"),
    "remove": ("delete", "trash", "bulk-delete"),
    "import": ("upload", "create", "file"),
    "ingest": ("upload", "import", "file"),
    "asynchronous": ("async", "job", "wait"),
    "async": ("job", "wait", "poll"),
    "poll": ("job", "wait", "status"),
    # "API keys" in the app (Settings > API keys) are client apps; `external-key`
    # holds other services' keys and wrongly won "list active API keys".
    "api": ("client-app",),
    "key": ("client-app",),
    "keys": ("client-app",),
    # "What did I ask you earlier?" is a past-conversation lookup: an agent
    # session. Nothing in `agent.session.list`/`agent.session.messages` text
    # says "conversation", "chat", or "history", so a query phrased that way
    # (rather than with the literal word "session") never found them.
    "conversation": ("session",),
    "conversations": ("session",),
    "chat": ("session",),
    "chats": ("session",),
    "history": ("session",),
    "previous": ("session",),
    "earlier": ("session",),
    "asked": ("session",),
    # British spellings search the same as the American ones.
    "summarise": ("summarize",),
    "standardise": ("standardize",),
    "normalise": ("normalize",),
    "categorise": ("categorize",),
}
_DISCOVERY_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "me",
        "please",
        "for",
        "to",
        "of",
        "by",
        "with",
        "can",
        "i",
        # Filler in goal phrasing ("merge my two datasets"); a command never
        # turns on these words, so they must not sink an otherwise good match.
        "my",
        "our",
        "one",
        "two",
        "another",
        "other",
        "into",
        "from",
        "and",
        # Same as "and" -- an incidental conjunction ("Power BI or Tableau")
        # must not become a required match term.
        "or",
        "all",
        "each",
        "this",
        "that",
        "how",
        "what",
        "is",
        # The tail of "what's"/"it's" once the apostrophe splits the word.
        "s",
        "do",
        "want",
        "need",
        "using",
        "than",
        "via",
        # Filler prepositions in goal phrasing ("datasets as rows", "datasets
        # in a project", "join two datasets on a key"); no command turns on
        # any of these.
        "as",
        "in",
        "on",
    }
)
# How many near misses a search with no full match returns.
_MAX_SUGGESTIONS = 5
# Cap on the curated purpose text a match's ``matched_on`` field quotes back,
# so one long entry can't bloat every result in a page.
_MATCHED_ON_MAX_CHARS = 120
# T1-R-06: an agent reading "No command matched every word" stopped there and
# never tried what 'suggestions' actually held (automation.create among
# them) -- the framing read as a dead end even when it wasn't one. Word the
# two cases (some candidates vs. none at all) differently so the presence of
# 'suggestions' reads as "try these" rather than "nothing found".
_NO_MATCH_HINT_WITH_SUGGESTIONS = (
    "No single command matched every word, but 'suggestions' lists the closest candidates "
    "-- each with its own matched_terms. Try one of those before rephrasing."
)
_NO_MATCH_HINT_NO_SUGGESTIONS = (
    "No command matched any word; try fewer or other words. 'mammoth view transform --help' "
    "lists every data transformation (join, pivot, filter, dedupe, math, ...), and 'mammoth "
    "schema list' is the complete inventory."
)
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@cache
def _operation_hints_by_command() -> dict[str, str]:
    """Return searchable OpenAPI summaries and tags keyed by command id."""
    hints: defaultdict[str, list[str]] = defaultdict(list)
    for operation in load_operations():
        command_id = operation.get("canonical_command")
        if not command_id:
            continue
        hints[str(command_id)].extend(
            [str(operation.get("summary", "")), *map(str, operation.get("tags", []))]
        )
    return {command_id: " ".join(parts) for command_id, parts in hints.items()}


def _accepted_fields(record: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Return the backing method's accepted fields for a command record.

    Args:
        record: A reviewed command manifest record.

    Returns:
        A list of ``{"name", "type", "required", "enum", "default"}`` field
        descriptors in signature order, or None when the command has no
        resolvable backing signature (bespoke commands) or accepts arbitrary
        keyword arguments.
    """
    contract = resolve_command_contract(str(record["command_id"]))
    if contract is None or contract.sdk_symbol is None:
        return None
    if contract.accepts_extra:
        return None
    excluded = _externally_supplied_fields(record["command_id"])
    body_schema = openapi_body_schema_for(
        tuple(str(item) for item in record.get("operation_ids", []))
    )
    return [
        {
            "name": field.name,
            "type": field.type_name,
            "required": field.required,
            "enum": field.enum_values,
            "default": field.default_value if field.has_default else None,
            "schema": (
                body_schema
                if field.name == "body"
                and is_opaque_mapping(field.annotation)
                and body_schema is not None
                else json_schema(field.annotation, field.name)
            ),
        }
        for field in contract.accepted_fields
        if field.name not in excluded
    ]


def _compact_accepted_fields(record: dict[str, Any]) -> list[dict[str, Any]] | None:
    """``_accepted_fields`` without the per-field JSON Schema.

    A find result inlines this for its top matches: enough to compose a call
    (name, type, required, enum) without the nested-schema detail ``schema
    get`` returns.
    """
    fields = _accepted_fields(record)
    if fields is None:
        return None
    return [{key: field[key] for key in ("name", "type", "required", "enum")} for field in fields]


def _externally_supplied_fields(command_id: str) -> frozenset[str]:
    """Fields supplied by positionals or authenticated CLI context."""
    if command_id in LOCAL_COMMANDS:
        return frozenset(
            {
                item.name
                for item in resolve_positionals(command_id)
                if item.falls_back_to_field is None
            }
        )
    excluded = excluded_input_fields(command_id)
    if command_id == "activity.list":
        # ``excluded_input_fields`` treats "project_id" as the active-project
        # context on every command, but here it is an ActivityFiltersSchema
        # request-body filter (any workspace project, not the active one) --
        # the command's own contract already admits and forwards it (see
        # ``_S7_ADDITIONAL_INPUT_FIELDS["activity.list"]``). Only
        # "workspace_id" is the legacy-admitted, never-forwarded field here.
        excluded -= {"project_id"}
    return excluded


def _positionals(command_id: str) -> list[dict[str, Any]]:
    """Return a command's positional arguments in the schema JSON shape."""
    return [spec.as_manifest() for spec in resolve_positionals(command_id)]


def _sample_positional_value(spec: PositionalSpec) -> Any:
    """A representative value for one positional, for the runnable example.

    Prefers the spec's ``example_value`` when set (a concrete, resolvable id for
    the discovery commands whose example is executed offline), falling back to a
    generic ``123``/``example`` placeholder that is never validated at build time.
    """
    if spec.example_value is not None:
        return spec.example_value
    return 123 if spec.type is int else _representative_string(spec.name)


def _sample_field_value(field: FieldSpec) -> Any:
    """A representative JSON value for one accepted field's type."""
    return _humanize_sample(sample_value(field.annotation), field.name)


def _representative_string(field_name: str) -> str:
    """Return a realistic, non-secret sample for a named string field."""
    name = field_name.casefold().replace("-", "_")
    if any(part in name for part in ("password", "secret", "token", "credential")):
        return "replace-with-secret"
    if "email" in name:
        return "analyst@example.com"
    if any(part in name for part in ("url", "uri", "webhook")):
        return "https://example.com/data.csv"
    if any(part in name for part in ("file", "path")):
        return "./sales.csv"
    if any(part in name for part in ("expression", "formula")):
        return "price * quantity"
    if any(part in name for part in ("query", "sql")):
        return "SELECT region, SUM(revenue) FROM data GROUP BY region"
    if any(part in name for part in ("prompt", "intent", "question", "message")):
        return "Summarize revenue by region"
    if any(part in name for part in ("new_column", "as_name", "name", "title", "label")):
        return "Revenue report"
    if "column" in name or name in {"source", "key"}:
        return "Status"
    if name.endswith("_id") or name in {"id", "identifier"}:
        return "resource-123"
    return "sample"


def _humanize_sample(value: Any, field_name: str) -> Any:
    """Replace generator placeholders with domain-shaped representative data."""
    if value == "example":
        return _representative_string(field_name)
    if isinstance(value, list):
        singular = field_name[:-1] if field_name.endswith("s") else field_name
        return [_humanize_sample(item, singular) for item in value]
    if isinstance(value, dict):
        return {
            ("sample_key" if key == "example" else key): _humanize_sample(
                item, "key" if key == "example" else key
            )
            for key, item in value.items()
        }
    return value


def _tokens(value: str) -> frozenset[str]:
    """Tokenize search text consistently across platforms and Python runs.

    A hyphenated word is kept whole and also split into its parts, so that
    ``date`` finds ``extract-date`` and ``date-diff`` as well as ``convert-type``'s
    example text.
    """
    tokens: set[str] = set()
    for token in _TOKEN_RE.findall(value.casefold()):
        tokens.add(token)
        if "-" in token:
            tokens.update(token.split("-"))
    return frozenset(tokens)


def _query_tokens(query: str) -> tuple[str, ...]:
    # Bare numbers ("top 10") are values, not intent words.
    return tuple(
        token
        for token in _tokens(query)
        if token not in _DISCOVERY_STOPWORDS and not token.isdigit()
    )


def _token_aliases(token: str) -> frozenset[str]:
    """Return the finite synonym neighborhood for one intent token."""
    return frozenset((token, *_DISCOVERY_SYNONYMS.get(token, ())))


def _adjacent_compound_forms(terms: tuple[str, ...]) -> dict[str, frozenset[str]]:
    """Map each query term to the compound spellings an adjacent pair makes.

    A route's un-hyphenated compound name (``powerbi``, ``bigquery``,
    ``onedrive``, ``sharepoint``, ...) never shares a token with the natural
    two-word phrasing a user types ("power bi", "big query"), since neither
    half is a substring match in the token-set membership test. Generalizes
    over any adjacent pair rather than hardcoding destination names: "azure
    blob" -> "azureblob"/"azure-blob", "share point" -> "sharepoint", and so
    on for whatever the query happens to contain.
    """
    forms: dict[str, set[str]] = {}
    for left, right in zip(terms, terms[1:], strict=False):
        for compound in (left + right, f"{left}-{right}"):
            forms.setdefault(left, set()).add(compound)
            forms.setdefault(right, set()).add(compound)
    return {term: frozenset(compounds) for term, compounds in forms.items()}


@cache
def _command_vocabulary_tokens() -> frozenset[str]:
    """Every token that names a command or appears in its curated purpose text.

    Distinguishes genuine CLI vocabulary from a data word -- a column,
    table, or other business noun from the caller's own data (``orders``,
    ``revenue``, ``store``) -- riding along in a goal. Counts a command's own
    id/path (``user``, ``workspace``, ``invoice`` are real resource nouns a
    command is named after) plus ``_COMMAND_DISCOVERY_PURPOSES``/
    ``_GROUP_DISCOVERY_PURPOSES`` -- text hand-curated specifically to
    describe what a command is for. Deliberately excludes ``human_example``/
    ``agent_example`` and OpenAPI-derived operation hints: those are
    illustrative sample values (a placeholder project name like "Revenue
    report", a sample filename like "sales.csv") reused verbatim across
    dozens of unrelated commands, so counting them would make almost any
    plausible business noun look like real vocabulary and defeat this
    check. A term absent from this set is not something any command is
    named after or actually about, so :func:`find_schemas` drops it from a
    goal's required terms rather than letting it sink an otherwise complete
    match.
    """
    vocabulary: set[str] = set()
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        command_id = str(record["command_id"])
        command_path = str(record["command_path"])
        text = (
            f"{command_id} {command_path} "
            f"{_COMMAND_DISCOVERY_PURPOSES.get(command_id, '')} "
            f"{_GROUP_DISCOVERY_PURPOSES.get(command_path.split()[0], '')}"
        )
        vocabulary.update(_tokens(text))
    return frozenset(vocabulary)


def _compact_contract(record: dict[str, Any]) -> dict[str, Any]:
    """Return the bounded, honest contract used by discovery clients.

    The manifest is authoritative for these values.  ``None`` is retained for
    fields the manifest does not prove; discovery must not turn a missing proof
    into a promise about backend behavior.
    """
    command_id = str(record["command_id"])
    resolved = resolve_command_contract(command_id)
    family = str(record.get("command_path", "")).split()[0]
    operation_hints = _operation_hints_by_command().get(command_id, "")
    search_text = f"{command_id} {family} {operation_hints}".casefold()
    if family == "dashboard" and command_id.startswith("dashboard.tags."):
        scope = "workspace"
    elif (
        command_id == "ai.retention.condition"
        or "{project_id}" in search_text
        or family
        in {
            "project",
            "dataset",
            "file",
            "folder",
            "view",
            "batch",
            "annotation",
            "dashboard",
            "automation",
            "schedule",
            "snippet",
            "template",
            "workflow",
        }
    ):
        scope = "project"
    elif "{workspace_id}" in search_text or family in {
        "workspace",
        "user",
        "support",
        "billing",
        "connector",
        "client-app",
        "external-key",
    }:
        scope = "workspace"
    elif family in {
        "auth",
        "config",
        "context",
        "completion",
        "doctor",
        "schema",
        "capability",
        "skill",
        "version",
    }:
        scope = "local"
    else:
        scope = "profile"

    # Policy values exposed by discovery come from the same resolved contract
    # consumed by admission/binding.  The manifest fallback only applies to
    # genuinely local/bespoke commands without a resolvable SDK contract.
    mutation_class = resolved.effects if resolved is not None else record.get("mutation_class")
    result_model = resolved.result_contract if resolved is not None else record.get("result_model")
    wait_policy = resolved.wait_behavior if resolved is not None else record.get("wait_policy")
    if mutation_class in {None, "read"}:
        recovery = "Rerun only after checking the exit code and stable error code."
    else:
        recovery = (
            "Reconcile target/job state before retry; retain returned IDs and verify "
            "the intended postcondition."
        )
    restrictions = record.get("known_restrictions")
    if edits_view_in_place(record):
        restrictions = f"{IN_PLACE_RECIPE} {restrictions or ''}".strip()
    elif restrictions is None:
        required_positionals = [
            str(item.get("metavar") or item.get("name"))
            for item in record.get("positionals", [])
            if item.get("required")
        ]
        if required_positionals:
            restrictions = "Required inputs: " + ", ".join(required_positionals) + "."
    return {
        "scope": scope,
        "effects": mutation_class,
        "preconditions": restrictions,
        "result": result_model,
        "async": wait_policy,
        "verification": record.get("acceptance_evidence"),
        "recovery": recovery,
        "limits": {
            "pagination": record.get("pagination_policy"),
            "continuation": (
                "not_proven" if record.get("pagination_policy") not in {None, "none"} else None
            ),
        },
    }


def _scope_requirements(command_id: str, scope: str) -> dict[str, Any]:
    """Return detailed binding facts without expanding compact discovery."""
    return _SCOPE_REQUIREMENTS.get(
        command_id,
        {
            "kind": scope,
            "required_context": [],
            "target_fields": [],
            "target_rule": (
                "Inspect positionals and accepted_fields for operation-specific bindings."
            ),
        },
    )


# Public name for callers that want contract semantics without rebuilding a
# full request schema.  The underscore implementation keeps the helper's
# origin obvious next to the manifest-derived schema code.
compact_contract = _compact_contract


def runnable_example(
    record: dict[str, Any],
    symbol: str | None,
    positionals: tuple[PositionalSpec, ...] | None = None,
) -> str | None:
    """Build one complete, copy-pasteable command line for this command.

    Args:
        record: A reviewed command manifest record.
        symbol: The command's ``sdk_symbol``, or None.

    Returns:
        A ``mammoth ...`` command line covering every required positional and
        required ``--input`` field; or None
        when the command has no resolvable backing signature.
    """
    if not symbol:
        return None
    # Credential documents must never be synthesized into a JSON command
    # example.  The local auth adapter validates a protected file reference;
    # the manifest carries the safe ``creds.json`` invocation instead.
    if record["command_id"] == "auth.login":
        return None
    if record["command_id"] == "ai.retention.condition":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"mode": "generate", "intent": "completed payments older than 90 days"}),
                *_OUTPUT_JSON_NO_INPUT,
                "--project",
                "456",
            ]
        )
    if record["command_id"] == "dashboard.import-workbook":
        # This high-impact multipart command needs explicit scope and target
        # confirmation in its unattended example. The numeric project is
        # syntactically runnable; the sample workbook remains nonexistent.
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "sample.twbx",
                "--project",
                "456",
                "--yes",
                "--confirm",
                "456",
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    # The backend's generic task_spec envelope is intentionally opaque in the
    # SDK signature. Keep the generated example structurally valid, while
    # agent-facing docs direct users to typed view.transform.* commands.
    task_examples = {
        "view.task.add": ["mammoth", "view", "task", "add", "123"],
        "view.task.preview": ["mammoth", "view", "task", "preview", "123"],
        "view.task.update": ["mammoth", "view", "task", "update", "123", "123"],
    }
    if record["command_id"] in task_examples:
        # COPY follows the backend param template (a list of SOURCE/AS items
        # with VERSION 2); the former ``COPY: {}`` placeholder was rejected
        # with backend code 720.
        task_input: dict[str, Any] = {
            "task_spec": {
                "DATAVIEW_ID": 123,
                "SEQUENCE_NUMBER": 1,
                "COPY": [
                    {
                        "SOURCE": "column_1",
                        "AS": {
                            "COLUMN": "Copy of column 1",
                            "TYPE": "TEXT",
                            "INTERNAL_NAME": "column_9",
                        },
                    }
                ],
                "VERSION": 2,
            }
        }
        if record["command_id"] == "view.task.update":
            task_input["dataset_id"] = 456
        return shlex.join(
            [
                *task_examples[record["command_id"]],
                "--input",
                json.dumps(task_input),
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] in _FIXED_EXAMPLES:
        positional_samples, sample_input = _FIXED_EXAMPLES[record["command_id"]]
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                *positional_samples,
                *(["--input", json.dumps(sample_input)] if sample_input else []),
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] == "batch.create-spec":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"file_id": 94}),
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] == "view.data.aggregate":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps(
                    {
                        "group_by": ["Channel"],
                        "aggregations": [
                            {"column": "Spend", "function": "SUM", "as_name": "Total Spend"}
                        ],
                    }
                ),
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] == "view.exportable-config.get":
        return shlex.join(
            ["mammoth", *record["command_path"].split(), "123", *_OUTPUT_JSON_NO_INPUT]
        )
    if record["command_id"] == "view.exportable-config.apply":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input-format",
                "json",
                "--input",
                json.dumps({"config": {"tasks": []}}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.rename":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"name": "Revenue"}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.set":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"tags": ["Revenue"]}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.delete":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.merge":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"target_id": 456}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.archive":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"archived": True}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    contract = resolve_command_contract(str(record["command_id"]))
    if contract is None or contract.sdk_symbol is None or contract.accepts_extra:
        return None
    fields = contract.accepted_fields
    if positionals is None:
        positionals = resolve_positionals(record["command_id"])
    tokens: list[str] = ["mammoth", *record["command_path"].split()]
    tokens.extend(str(_sample_positional_value(p)) for p in positionals)
    excluded = frozenset(
        (set() if record["command_id"] in LOCAL_COMMANDS else {"project_id", "workspace_id"})
        | {item.name for item in positionals}
        # A positional may fill a differently-named SDK parameter (e.g. the
        # ``folder_id`` positional fills ``folder_ids``). That parameter is
        # positional-sourced, so it must be excluded from the generated
        # ``--input`` example too -- mirroring ``excluded_input_fields`` so the
        # example never advertises a field the validator rejects.
        | {item.fills_sdk_param for item in positionals if item.fills_sdk_param}
    ) | handler_owned_fields(record["command_id"])
    required = [field for field in fields if field.required and field.name not in excluded]
    hints = example_input_hints(record["command_id"])
    if required or hints:
        body_schema = openapi_body_schema_for(
            tuple(str(item) for item in record.get("operation_ids", []))
        )
        document = {
            field.name: (
                _humanize_sample(sample_from_schema(body_schema), field.name)
                if field.name == "body"
                and is_opaque_mapping(field.annotation)
                and body_schema is not None
                else _sample_field_value(field)
            )
            for field in required
        }
        # A command with a runtime "one of" / identifier requirement the signature
        # cannot express supplies the missing accepted field here, so the
        # documented example is actually runnable rather than just well-formed.
        document.update(hints)
        if set(record.get("secret_fields") or ()).intersection(document):
            tokens.extend(["--input", _PROTECTED_INPUT_PATH])
        else:
            tokens.extend(["--input", json.dumps(document)])
    tokens.extend(_OUTPUT_JSON_NO_INPUT)
    if record["command_id"] in {"project.user.update", "data-app.share", "workspace.user.add"}:
        # These published high-impact examples must satisfy the same policy
        # their manifests advertise; otherwise discovery emits a command that
        # deterministically fails before dispatch.
        tokens.append("--yes")
    if record["command_id"] in {
        "project.resource-dependencies.update",
        "dashboard.embed.key.rotate",
        "dashboard.embed.secret.rotate",
        "dashboard.embed.config.set",
        "dashboard.embed.origin.revoke",
        "dashboard.context.apply",
    }:
        # These commands have a confirm_target policy.  Keep their generated
        # example executable in non-interactive mode instead of advertising a
        # request that the safety guard will reject.
        tokens.extend(["--yes", "--confirm", str(_sample_positional_value(positionals[0]))])
    elif record["command_id"] == "dashboard.create-blank":
        tokens.append("--yes")
    return shlex.join(tokens)


def _schema_common(record: dict[str, Any]) -> dict[str, Any]:
    """Shared enrichment fields for both the listing and single-command views."""
    symbol = record.get("sdk_symbol")
    accepted = _accepted_fields(record)
    if accepted is not None and record["command_id"] in {
        "view.exportable-config.get",
        "view.exportable-config.apply",
    }:
        # The SDK requires a parent dataset, but the CLI resolves it from the
        # view or accepts it as an optional trailing positional/input field.
        accepted = [
            {**field, "required": False} if field["name"] == "dataset_id" else field
            for field in accepted
        ]
    input_schema = None
    if accepted is not None:
        definitions: dict[str, Any] = {}
        properties: dict[str, Any] = {}
        for field in accepted:
            field_schema = dict(field["schema"])
            prefix = f"{field['name']}__"

            def namespace_refs(value: Any, namespace: str = prefix) -> Any:
                if isinstance(value, dict):
                    return {
                        key: (
                            item.replace("#/$defs/", f"#/$defs/{namespace}")
                            if key == "$ref" and isinstance(item, str)
                            else namespace_refs(item)
                        )
                        for key, item in value.items()
                    }
                if isinstance(value, list):
                    return [namespace_refs(item) for item in value]
                return value

            def hoist_definitions(value: Any, namespace: str = prefix) -> Any:
                if isinstance(value, dict):
                    result = dict(value)
                    nested = result.pop("$defs", {})
                    for name, definition in nested.items():
                        definitions[f"{namespace}{name}"] = hoist_definitions(definition)
                    return {key: hoist_definitions(item) for key, item in result.items()}
                if isinstance(value, list):
                    return [hoist_definitions(item) for item in value]
                return value

            properties[field["name"]] = hoist_definitions(namespace_refs(field_schema))
        # A field a positional falls back to (the dual-sourced "positional OR
        # --input field" pattern) is satisfiable from the command line, so it is
        # NOT required *in the --input document*: the runnable example supplies
        # it positionally and omits it from --input, so requiring it here would
        # make the generated example fail its own input schema. It stays an
        # accepted (optional) field so passing it via --input still works.
        fallback_fields = {
            spec.falls_back_to_field
            for spec in resolve_positionals(record["command_id"])
            if spec.falls_back_to_field
        }
        input_schema = {
            "type": "object",
            "properties": properties,
            "required": [
                field["name"]
                for field in accepted
                if field["required"] and field["name"] not in fallback_fields
            ],
            "additionalProperties": False,
        }
        if record["command_id"] == "batch.create-spec":
            input_schema["oneOf"] = [
                {
                    "required": ["source_id", "mapping"],
                    "not": {"required": ["file_id"]},
                },
                {
                    "required": ["file_id"],
                    "not": {"anyOf": [{"required": ["source_id"]}, {"required": ["mapping"]}]},
                },
            ]
        if record["command_id"] == "view.exportable-config.apply":
            # Release schema: exactly one of clipboard items or full config.
            # Nested task/action/etc objects intentionally remain open because
            # their release schemas are polymorphic and operation-specific.
            input_schema = {
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "integer", "minimum": 1},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "params": {"type": "object", "additionalProperties": True},
                                "transform_params": {
                                    "type": "object",
                                    "additionalProperties": True,
                                },
                            },
                            "additionalProperties": True,
                        },
                    },
                    "config": {
                        "type": "object",
                        "properties": {
                            "tasks": {"type": ["array", "null"], "items": {"type": "object"}},
                            "actions": {"type": ["array", "null"], "items": {"type": "object"}},
                            "checkpoints": {
                                "type": ["array", "null"],
                                "items": {"type": "object"},
                            },
                            "data_checks": {
                                "type": ["array", "null"],
                                "items": {"type": "object"},
                            },
                            "derivatives": {
                                "type": ["array", "null"],
                                "items": {"type": "object"},
                            },
                            "display_properties": {"type": ["object", "null"]},
                            "metadata": {
                                "type": ["array", "null"],
                                "items": {"type": "object"},
                            },
                            "dependencies": {"type": ["object", "null"]},
                            "user_preferences": {"type": ["object", "null"]},
                            "name": {"type": ["string", "null"]},
                            "taskwise_info": {"type": ["object", "null"]},
                        },
                        "additionalProperties": True,
                    },
                    "insert_after_sequence": {"type": ["integer", "null"]},
                    "is_paste_mode": {"type": "boolean", "default": False},
                },
                "oneOf": [
                    {"required": ["items"], "not": {"required": ["config"]}},
                    {"required": ["config"], "not": {"required": ["items"]}},
                ],
                "additionalProperties": False,
            }
        if record["command_id"] == "dataset.batch-data":
            batch_properties = cast(dict[str, Any], input_schema["properties"])
            batch_properties["limit"].update({"minimum": 0, "maximum": 100})
            batch_properties["offset"].update({"minimum": 0})
            for field in accepted:
                if field["name"] == "limit":
                    field["schema"].update({"minimum": 0, "maximum": 100})
                elif field["name"] == "offset":
                    field["schema"].update({"minimum": 0})
        if definitions:
            input_schema["$defs"] = definitions
        # This mapping is produced locally from reviewed command contracts,
        # not returned by an API. Preserve JSON-Schema declaration names (for
        # example ``properties.api_secret``) through Result/render's second
        # normalization pass without trusting arbitrary result dictionary keys.
        input_schema = cast(dict[str, Any], trusted_json_schema(input_schema))
    contract = _compact_contract(record)
    opaque_fields = [
        str(field["name"])
        for field in accepted or []
        if str(field["name"]) in {"task_spec", "body"}
    ]
    contract_level = (
        "opaque_expert"
        if record["command_id"] in _OPAQUE_EXPERT_COMMANDS
        else "partially_typed" if opaque_fields else "typed"
    )
    return {
        "positionals": _positionals(record["command_id"]),
        "accepted_fields": accepted,
        "input_schema": input_schema,
        "runnable_example": runnable_example(record, str(symbol) if symbol else None),
        # Keep the contract alongside the detailed schema so callers can stop
        # after one bounded request when they only need execution semantics.
        "contract": contract,
        "contract_level": contract_level,
        "unresolved_nested_fields": opaque_fields,
        "safe_typed_alternatives": (
            list(_TYPED_TRANSFORM_ALTERNATIVES)
            if record["command_id"] in _OPAQUE_EXPERT_COMMANDS
            else []
        ),
        # Top-level aliases keep the compact contract easy to consume while
        # ``contract`` gives clients one stable namespace for future fields.
        **contract,
    }


def schema_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        entries.append(
            {
                "command_id": record["command_id"],
                "command_path": record["command_path"],
                "request_model": record["request_model"],
                "result_model": record["result_model"],
                "options": record.get("options", []),
                **_schema_common(record),
                "mutation_class": record["mutation_class"],
                "confirmation": record["confirmation"],
                "wait_policy": record["wait_policy"],
                "pagination_policy": record["pagination_policy"],
                "human_example": record["human_example"],
                "agent_example": record["agent_example"],
            }
        )
    return sorted(entries, key=lambda entry: entry["command_id"])


#: ``schema get`` fields an agent needs to compose one call. The rest of the
#: record (JSON Schema, exit-code table, recovery boilerplate) is static or
#: duplicated and comes back only with ``full``.
_BRIEF_SCHEMA_KEYS = (
    "command_id",
    "command_path",
    "positionals",
    "accepted_fields",
    "agent_example",
    "mutation_class",
    "confirmation",
    "wait_policy",
    "scope",
    "scope_requirements",
    "preconditions",
    "secret_fields",
    "safe_typed_alternatives",
)


def schema_index(family: str | None = None) -> dict[str, Any]:
    """Return the command index: families with counts, or one family's commands.

    The complete per-command records (``schema_entries``) run to megabytes;
    an agent choosing a command needs names and mutation classes, then one
    ``schema get`` for the command it picked.
    """
    entries = schema_entries()
    words = (family or "").strip().split(".")[0].split()
    if words:
        wanted = words[0]
        commands = [
            {
                "command_id": entry["command_id"],
                "command_path": entry["command_path"],
                "mutation_class": entry["mutation_class"],
                "confirmation": entry["confirmation"],
            }
            for entry in entries
            if entry["command_path"].split()[0] == wanted
        ]
        return {"family": wanted, "total": len(commands), "commands": commands}
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["command_path"].split()[0]] = (
            counts.get(entry["command_path"].split()[0], 0) + 1
        )
    return {
        "total": len(entries),
        "families": [{"family": name, "commands": count} for name, count in sorted(counts.items())],
        "next": "mammoth schema list FAMILY, then mammoth schema get COMMAND_ID",
    }


def _is_scalar_field_schema(schema: Any) -> bool:
    """Whether a field's JSON Schema is a plain scalar with no nested shape.

    A caller composing ``--input`` for a scalar field just needs its type
    name. An object, an array of objects, or a union that includes an
    object (e.g. increment-date's ``delta``, convert-type's
    ``conversions``, a ``condition``) needs its nested shape too, or the
    bare type name (``DateDelta``) leaves it to guess.
    """
    if not isinstance(schema, dict):
        return True
    branches = schema.get("anyOf") or schema.get("oneOf")
    if branches:
        return all(_is_scalar_field_schema(branch) for branch in branches)
    schema_type = schema.get("type")
    if schema_type == "object":
        return False
    if schema_type == "array":
        return _is_scalar_field_schema(schema.get("items"))
    return True


def brief_schema(entry: dict[str, Any]) -> dict[str, Any]:
    """Reduce a full ``schema get`` record to what composing one call needs."""
    brief = {key: entry[key] for key in _BRIEF_SCHEMA_KEYS if key in entry}
    accepted = brief.get("accepted_fields")
    if isinstance(accepted, list):
        # Type and requirement are what a caller reads for a scalar; a
        # non-scalar field keeps its JSON Schema too, since a bare type name
        # does not say what shape it needs. ``full`` still has everything.
        brief["accepted_fields"] = [
            {
                key: value
                for key, value in field.items()
                if key != "schema" or not _is_scalar_field_schema(field.get("schema"))
            }
            for field in accepted
            if isinstance(field, dict)
        ]
    brief["full"] = f"mammoth schema get {entry['command_id']} --input '{{\"full\": true}}'"
    return brief


def _inline_call_detail(entries: list[dict[str, Any]]) -> None:
    """Add each entry's compact accepted fields and agent example in place."""
    for entry in entries:
        record = command_by_id(entry["command_id"])
        if record is None:
            continue
        fields = _compact_accepted_fields(record)
        if fields is not None:
            entry["accepted_fields"] = fields
        if record.get("agent_example"):
            entry["agent_example"] = record["agent_example"]


def _inline_picks(page: list[dict[str, Any]], offset: int) -> list[dict[str, Any]]:
    """The entries to inline: the top ones, plus read commands ranked below a write.

    A read that answers the question is worth its fields even when a write such as
    ``view.transform.pivot`` outranks it; otherwise the caller needs a ``schema get``.
    """
    head = page[: max(0, _INLINE_DETAIL_COUNT - offset)]
    reads = [
        entry
        for entry in page[len(head) :]
        if (command_by_id(entry["command_id"]) or {}).get("mutation_class") == "read"
    ]
    return head + reads[:_INLINE_DETAIL_COUNT]


#: How to drill down from a find: a family's full command list, or every family.
_BROWSE_NEXT = (
    "mammoth schema list FAMILY lists every command in a family; mammoth schema list "
    "lists the families"
)


def find_schemas(
    query: str,
    *,
    limit: int = _MAX_FIND_RESULTS,
    cursor: int = 0,
) -> dict[str, Any]:
    """Return compact command matches for interactive and agent discovery.

    ``schema list`` deliberately remains the complete, machine-readable
    inventory.  This search avoids returning a large nested schema for every
    command when callers only need to locate the right command id first; use
    the included ``full_schema_command`` to fetch the authoritative detail.
    Every whitespace-separated term must occur in a command name, its examples,
    or its stable operation-purpose text, making the result deterministic and
    easy to compose in scripts.  When no command carries every term, the result
    adds ``suggestions`` (the commands that carry the most terms) and a ``hint``,
    so a cold caller who phrased the goal in other words is not left with an
    empty list.
    """
    # A query made only of filler words keeps them, rather than matching
    # every command.
    raw_terms = _query_tokens(query) or tuple(_tokens(query))
    compound_forms = _adjacent_compound_forms(raw_terms)
    # A term no command's discovery-purpose text would ever say is a data
    # word (a column/table/business noun from the caller's own data, not CLI
    # vocabulary) riding along in the goal; drop it before the all-terms
    # rule and scoring so it can't sink an otherwise complete match. If
    # every term would be dropped, keep them all -- a query that is nothing
    # but data words still deserves its ordinary near-miss treatment rather
    # than becoming a match-everything wildcard. A literal full-path lookup
    # (the ``named`` check below) always uses the un-dropped ``raw_terms``,
    # so naming a command by its exact path never depends on this filter.
    vocabulary = _command_vocabulary_tokens()
    cli_terms = tuple(
        term
        for term in raw_terms
        if (_token_aliases(term) & vocabulary)
        or (compound_forms.get(term, frozenset()) & vocabulary)
    )
    terms = cli_terms or raw_terms
    query_cf = query.casefold()
    # Clamp caller-provided bounds instead of allowing an accidental unbounded
    # discovery response.  A negative cursor is a usage mistake, not a request
    # to wrap around the catalog.
    bounded_limit = max(1, min(int(limit), _MAX_FIND_LIMIT))
    offset = max(0, int(cursor))
    ranked_matches: list[tuple[int, dict[str, Any]]] = []
    near_misses: list[tuple[int, int, dict[str, Any], list[str]]] = []
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        command_id = str(record["command_id"])
        command_path = str(record["command_path"])
        positional_help = " ".join(
            str(positional.get("help", "")) for positional in record.get("positionals", [])
        )
        primary_text = f"{command_id} {command_path}".casefold()
        sources = (
            (30, f"{record.get('human_example', '')} {record.get('agent_example', '')}"),
            (20, positional_help),
            (15, _operation_hints_by_command().get(command_id, "")),
            (15, _IN_PLACE_KEYWORDS if edits_view_in_place(record) else ""),
            (60, _COMMAND_DISCOVERY_PURPOSES.get(command_id, "")),
            (3, _GROUP_DISCOVERY_PURPOSES.get(command_path.split()[0], "")),
        )
        searchable = " ".join(source for _, source in sources).casefold()
        searchable_tokens = _tokens(f"{primary_text} {searchable}")
        matched_terms = [
            term
            for term in terms
            if (_token_aliases(term) & searchable_tokens)
            or (compound_forms.get(term, frozenset()) & searchable_tokens)
        ]
        if not matched_terms:
            continue
        score = 0
        for term in matched_terms:
            if term in _tokens(primary_text):
                score += 100
            elif term in _tokens(searchable):
                score += 40
            else:
                score += 20
            # Exact phrase/path matches outrank a synonym match, then stable
            # command-id ordering breaks all remaining ties.
            if term in searchable_tokens:
                score += 10
        # Purpose and command-specific hints are stronger than generic
        # family words such as ``data`` or ``show``.
        score += 5 * sum(
            1
            for term in matched_terms
            if any(term in source.casefold() for _, source in sources[:2])
        )
        command_purpose = _COMMAND_DISCOVERY_PURPOSES.get(command_id, "").casefold()
        score += 100 * sum(1 for term in matched_terms if term in _tokens(command_purpose))
        action = command_path.split()[1] if len(command_path.split()) > 1 else ""
        if "show" in matched_terms and action in {"list", "get", "browse"}:
            score += 80
        new_object = _NEW_OBJECT_HINTS.get(command_id)
        if new_object and re.search(rf"\bnew\s+{new_object}s?\b", query_cf):
            score += _OBJECT_ADJACENCY_BOOST
        existing_object = _EXISTING_OBJECT_HINTS.get(command_id)
        if existing_object and re.search(rf"\bexisting\s+{existing_object}s?\b", query_cf):
            score += _OBJECT_ADJACENCY_BOOST
        is_support = command_id.startswith("support.")
        entry = {
            "command_id": command_id,
            "command_path": command_path,
            "mutation_class": record["mutation_class"],
            "confirmation": record["confirmation"],
            "full_schema_command": f"mammoth schema get {command_id}",
        }
        # A match on hidden curated purpose text (T1-I-07) is otherwise
        # invisible to the caller: only command_id/command_path/matched_terms
        # come back, and a terse docstring-derived example can read as
        # something else entirely (connector.ai.chat's own example reads as
        # "ask the AI a question", not "build a connector for an unsupported
        # API"). Echo the purpose text that matched, capped so a long entry
        # doesn't bloat every result.
        if command_purpose and any(term in _tokens(command_purpose) for term in matched_terms):
            purpose_text = _COMMAND_DISCOVERY_PURPOSES[command_id]
            entry["matched_on"] = (
                purpose_text
                if len(purpose_text) <= _MATCHED_ON_MAX_CHARS
                else purpose_text[:_MATCHED_ON_MAX_CHARS].rstrip() + "..."
            )
        if is_support:
            # These operate on another workspace/customer on the caller's
            # behalf (Mammoth-operator tooling), not the caller's own
            # workspace. A query that also has an ordinary match should
            # never surface the operator command first.
            entry["operator_only"] = (
                "support.* commands act on another workspace as an operator, not the "
                "caller's own; ordinary workspace work uses the non-support command."
            )
        # A query that spells out this command's whole path (``aggregate view
        # data ...``) asks for it by name, whatever goal words ride along.
        path_tokens = set(_tokens(command_path))
        named = len(path_tokens) >= 3 and path_tokens <= set(raw_terms)
        if named:
            score += _NAMED_COMMAND_BOOST
        if named or len(matched_terms) == len(terms):
            ranked_matches.append((score, entry))
        else:
            near_misses.append((len(matched_terms), score, entry, matched_terms))
    ranked_matches.sort(
        key=lambda item: (
            item[1]["command_id"].startswith("support."),
            -item[0],
            item[1]["command_id"],
        )
    )
    total_matches = len(ranked_matches)
    page = [match for _, match in ranked_matches[offset : offset + bounded_limit]]
    _inline_call_detail(_inline_picks(page, offset))
    has_more = offset + len(page) < total_matches
    continuation = (
        {
            "next_cursor": str(offset + len(page)),
            "has_more": True,
            "limit": bounded_limit,
            "query": query,
        }
        if has_more
        else None
    )
    result: dict[str, Any] = {
        "query": query,
        "matches": page,
        "total_matches": total_matches,
        "truncated": has_more,
        "continuation": continuation,
    }
    if total_matches == 0:
        # Most terms first, then the ordinary score: a command that carries
        # two of three words beats one that carries a single common word.
        near_misses.sort(key=lambda item: (-item[0], -item[1], item[2]["command_id"]))
        result["suggestions"] = [
            {**entry, "matched_terms": matched}
            for _, _, entry, matched in near_misses[:_MAX_SUGGESTIONS]
        ]
        # A goal phrased in the user's words rarely carries every term; the
        # best near misses still say how to call them, so one find suffices.
        _inline_call_detail(result["suggestions"][:_INLINE_DETAIL_COUNT])
        result["hint"] = (
            _NO_MATCH_HINT_WITH_SUGGESTIONS
            if result["suggestions"]
            else _NO_MATCH_HINT_NO_SUGGESTIONS
        )
    result["browse"] = _browse(page or result.get("suggestions", []))
    return result


def _browse(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """The families behind *entries* and how to list each one in full: a keyword
    find surfaces one way to do a thing, its family holds the siblings."""
    families = list(dict.fromkeys(entry["command_path"].split()[0] for entry in entries))
    return {"families": families, "next": _BROWSE_NEXT}


def get_schema(command_id: str) -> dict[str, Any] | None:
    record = command_by_id(command_id)
    if record is None or record.get("disposition") == "alias":
        return None
    common = _schema_common(record)
    return {
        "command_id": record["command_id"],
        "command_path": record["command_path"],
        "request_model": record["request_model"],
        "result_model": record["result_model"],
        "options": record.get("options", []),
        **common,
        "scope_requirements": _scope_requirements(command_id, str(common["scope"])),
        # ``schema list`` already exposed these execution controls.  Keep the
        # detail endpoint self-sufficient so an agent does not need a second
        # inventory lookup before deciding whether it may dispatch.
        "mutation_class": record["mutation_class"],
        "confirmation": record["confirmation"],
        # Named so a caller knows which fields must arrive through a protected
        # ``--input FILE`` rather than an inline document or argv.
        "secret_fields": list(record.get("secret_fields") or ()),
        "wait_policy": record["wait_policy"],
        "pagination_policy": record["pagination_policy"],
        "human_example": record["human_example"],
        "agent_example": record["agent_example"],
        "exit_codes": {
            "0": "success",
            "1": "API or operation failure",
            "2": "usage, input, or confirmation failure",
            "4": "authentication or authorization failure",
            "5": "resource not found",
            "6": "conflict or failed precondition",
            "7": "retryable network, timeout, or rate-limit failure",
            "130": "interruption",
        },
    }
