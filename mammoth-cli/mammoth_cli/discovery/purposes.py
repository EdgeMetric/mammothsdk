"""Hand-written purpose text that ``schema find`` matches a goal against.

The text supplements (never replaces) the manifest and OpenAPI text of each command.
"""

from __future__ import annotations

# Human intent often uses the resource's familiar format or outcome rather
# than a literal command token.  These small, stable hints supplement (never
# replace) manifest and OpenAPI text during compact discovery.
GROUP_DISCOVERY_PURPOSES = {
    "dataset": "data import tables CSV spreadsheet",
    "file": "source file storage",
    "view": "transform query clean analyze data pipeline",
    "dashboard": "build visualize share chart charts report analytics",
    "workflow": "automate pipeline orchestration",
}

COMMAND_DISCOVERY_PURPOSES = {
    "view.update": "rename change name to a new name title relabel",
    "view.explore-panel.get": "explore cards saved panel the data editor explore side panel read",
    "view.explore-panel.set": "open show explore cards for all or some columns, replace the panel",
    "view.explore-panel.edit": (
        "change an explore card: metric sum average, sort, list or chart layout, level, filter "
        "or exclude values, clear, drop a card, search, scatter, ask a question"
    ),
    "view.explore-panel.add-to-dashboard": (
        "put an explore card on a dashboard, the card menu add to dashboard, new blank board"
    ),
    "view.explore-panel.export-image": (
        "export explore card as image, save explore chart as png or svg, a picture of one card "
        "with the rows"
    ),
    "dashboard.figure.add": (
        "append an explore card figure tile to a dashboard from a payload, no chat turn"
    ),
    "file.upload": (
        "upload import CSV spreadsheet XLSX source data append add rows union stack "
        "a file into an existing dataset excel workbook tabs sheets drop in"
    ),
    "file.upload-folder": (
        "upload source-data directory folder a folder of files every file in a local folder"
    ),
    # A "folder" in Mammoth is a project folder that groups datasets, views and
    # dashboards (`folder` commands); a local directory of files is `file upload-folder`.
    # An uploaded file becomes a dataset named after it, so deleting it is `dataset delete`.
    "folder.list": "list show folder folders directories organize project resources",
    "folder.create": "create make new add folder directory organize project resources",
    "folder.update": "rename folder directory",
    "folder.move": "move put dataset view dashboard resources into a folder directory",
    "file.delete": "delete remove uploaded source file csv",
    "file.list": "list show uploaded source files csv",
    "view.export.csv": "export download local CSV file artifact",
    "view.export.download": (
        "export download local file artifact xlsx excel json ndjson xml yaml parquet "
        "file type format"
    ),
    "view.export.dataset": (
        "send copy branch out create save the result rows into a new project from an "
        "existing append appending union stack monthly rows across datasets views "
        "vertically vertical below on top of stacked union all"
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
    "view.export.live-link": "live link add create public url share link always latest shareable",
    "view.export.mssql": "sql server mssql microsoft database",
    "view.export.mysql": "mysql database",
    "view.export.onedrive": "one drive onedrive microsoft cloud storage",
    "view.export.postgres": (
        "postgres postgresql database your own server; "
        "for the Postgres Mammoth hosts, use publish-db"
    ),
    "view.export.powerbi": "power bi powerbi microsoft dashboard workspace",
    "view.export.publish-db": (
        "publish database live connection odbc bi tool reads table point straight at always latest "
        "postgres managed mammoth managed write into our sql database"
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
    "view.transform.batch": (
        "batch several transforms together in one call one pipeline run chain steps at once"
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
        "conditional threshold greater than if text times parameter {name} variable"
    ),
    "view.transform.pivot": (
        "pivot table group by aggregate aggregation sum count average summary summarize "
        "summarise per region total"
    ),
    "view.transform.repeat-rows": (
        "repeat rows duplicate each row n times copies one row per value listed values "
        "date series one row per month day week explode into a series number range "
        "sequence generate dates"
    ),
    "view.transform.rename-columns": (
        "rename column columns header headers relabel change column name names title data"
    ),
    "view.column.format.set": (
        "format display column date format number format decimals decimal places currency "
        "symbol percent percentage thousands separator show dates as how values look grid "
        "date display"
    ),
    "view.conditional-format.replace": (
        "replace redo reset swap all conditional formatting rules highlight colour color "
        "existing rules in one call"
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
    "view.transform.first-name": "first name given name first word of a full name",
    "view.transform.update-column": "overwrite a column in place with an expression, one call",
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
    # Reads a column's value distribution: what is trending, how a column is
    # spread, its top values, a count over time. It opens no card in the UI.
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
    # The basic read: the first thing anyone asks of a view.
    "view.data.get": (
        "read show the rows of the table see data records preview browse fetch look at first rows "
        "page limit offset, read only"
    ),
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
    # "Check every source for missing values" spans datasets: the agent ran
    # view.data.profile once per view (17 calls, 125 s) where one stored-stats
    # read answers it (gap eval 10-10 S16).
    "dataset.column-stats": (
        "missing values blanks blank empty nulls null incomplete completeness data quality "
        "across every all dataset datasets source sources tables project which column "
        "columns worst most check"
    ),
    # "Why did store revenue drop from July to August?" took the agent 18
    # hand-built aggregates and 95 s (gap eval 10-10 S03); one drivers call
    # answers it with the totals, volume vs value and the top contributors.
    # Generic words (why, explain, rise, increase, month, quarter, period) are
    # left out: each would make other goals ("why is my pipeline failing",
    # "sales by quarter") need this text to match.
    "view.data.drivers": (
        "drop dropped fall fell fallen decline declined decreased increased rose grew drove "
        "drivers driver between contributors contributed"
    ),
    # "Forecast store revenue for October 2026" made the agent divide a partial
    # September by its days (gap eval 10-10 S20); forecast fits a trend to the
    # complete periods and gives a range. Generic words (will, estimate, next,
    # month) are left out: each would make other goals need this text to match.
    "view.data.forecast": (
        "forecast forecasts forecasting projection projections projected predict prediction "
        "future"
    ),
    # What a term means for one dataset (gap proposal P13): said once, used by
    # every chat on it. "remember that churned means" is a definition, not a
    # preference (project.memory.add) or a board rule (dashboard.context.create).
    "dataset.definition.add": (
        "save remember define definition what a word means meaning counts as for this dataset"
    ),
    "dataset.definition.list": "definitions meanings glossary saved for a dataset",
    "dataset.definition.remove": "forget a definition meaning glossary term",
    # Goals users state in their own words, one entry per command the agent's
    # system prompt used to spell out by hand.
    "dashboard.suggestion.list": "ideas suggest suggestions what to show put on a board chart",
    "dashboard.analytics": "who viewed seen opened views visitors usage of a board",
    "dashboard.share": (
        "share make live publish board for the team link access with a user person "
        "colleague invite grant email address"
    ),
    "dashboard.delete": "delete remove permanently dashboard board",
    "view.delete": "delete remove permanently",
    "dataset.delete": "delete remove permanently dataset uploaded file csv",
    "view.list": "list all views",
    "view.task.delete": "undo remove the last step task from the pipeline revert a transformation",
    "view.data.query": "query rows with a filter condition sort columns and get rows back",
    "batch.create": "append add new data to an existing dataset",
    "auth.login": "log in sign in login authenticate token workspace",
    "auth.status": "who am i signed in logged in as current user session status check",
    "doctor": "check my setup health diagnose environment install doctor",
    # "Import a table from SQL Server / MySQL / Postgres into a dataset" is a
    # connector flow -- list connectors, create a connection, then a ds-config
    # (a table or query pulled in as a new dataset) -- but none of these
    # commands said "database", "table", "SQL Server" or "import", so every
    # phrasing missed them and only the unrelated view.export.* commands
    # (which push data OUT to a database) matched.
    "connector.list": (
        "connectors available sources database SQL Server MSSQL MySQL Postgres Oracle SFTP "
        "file server connect import pull load table file into dataset"
    ),
    "connector.get": (
        "connector database SQL Server MSSQL MySQL Postgres SFTP file server connection fields "
        "host port username password required to connect import table file dataset "
        "REST API Elasticsearch generic_rest_api config schema"
    ),
    "connector.connection.list": (
        "which outside external sources connected connections list database SQL Server "
        "MSSQL MySQL Postgres SFTP file server connector already connected import table "
        "file dataset"
    ),
    "connector.connection.get": (
        "connection database SQL Server MSSQL MySQL Postgres SFTP file server connector "
        "connected import table file dataset"
    ),
    "connector.connection.create": (
        "connect a database such as SQL Server MSSQL MySQL Postgres Oracle or an SFTP file "
        "server host port username password new connection connector to import a table or "
        "file into a dataset, or a REST API or Elasticsearch generic_rest_api base_url"
    ),
    "connector.ds-config.create": (
        "import pull load read retrieve a table or SQL query from a connected database such "
        "as SQL Server MSSQL MySQL Postgres connector connection as a new dataset rows data "
        "REST API Elasticsearch sample validate"
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
    "capabilities": (
        "cannot can't unsupported not supported limitation limitations gap gaps workaround "
        "instead missing feature what the cli cannot do yet"
    ),
    "how": (
        "how goal recipe steps order sequence of commands guide accomplish walkthrough "
        "plain language"
    ),
    "run": (
        "run batch many several multiple commands jsonl json lines file stdin one process "
        "faster fewer round trips script sequence loop bulk"
    ),
    "resolve": (
        "resolve name what is this dataset view project called named which kind "
        "ambiguous same name another project lookup identify"
    ),
    "dataset.schema-diff": (
        "compare two datasets columns added removed renamed before append batch mapping "
        "schema difference same columns different names"
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
    "agent.run.retry": "retry the failed run, try a second time, rerun after a failure or a stop",
    "agent.run.instance.list": "which agents sub agents helpers workers ran in this run instances",
    "agent.run.instance.messages": "which messages this agent of the run sent and received",
    "agent.run.instance.transcript": (
        "show the full transcript of one agent in the run model messages"
    ),
    "agent.run.units.list": (
        "which objects is the run working on units of work progress queued done failed"
    ),
    "agent.message.set-request-kind": (
        "wrong kind of request answered, correct the kind: ask insight build automate fix"
    ),
    "agent.plan.approve": "approve the agent plan go ahead and run the plan the agent proposed",
    "agent.plan.skip": "skip one step of the agent plan do not run that proposed step",
    "agent.plan.discard": "discard the agent plan reject everything the agent proposed",
    "agent.plan.edit-proposal": (
        "rename or remove a step in the plan proposal waiting workflow edit the plan"
    ),
    "dashboard.swap-fit": "which dataset fits this dashboard before swapping data score candidates",
    "dashboard.audience.get": "who opened my dashboard readers visitors audience over time",
    "dashboard.audience.summary": "how many people opened each dashboard in the library",
    "dashboard.audience.digest.get": "weekly audience email setting for a dashboard get",
    "dashboard.audience.digest.set": "turn the weekly audience email on or off for a dashboard",
    "dashboard.engagement.get": (
        "who opened my dashboard, how long readers read each page, reach engagement people visits"
    ),
    "dashboard.engagement.person": "visits by one person to my dashboard, when and how long read",
    "dashboard.engagement.remind": (
        "remind people to look at the dashboard, nudge by email readers who skipped the board"
    ),
    "dashboard.own-data.start": (
        "use my own data on a template board fit the template to my upload or dataset"
    ),
    "dashboard.own-data.status": "where the own-data run is, the stage and the proposal to review",
    "dashboard.own-data.preview": "preview the template board on my own data before accepting",
    "dashboard.own-data.accept": "apply the proposed board built from my upload",
    "dashboard.own-data.dismiss": "drop the pending own-data proposal and keep the template as is",
    "collection.create": (
        "group dashboards into a collection a set of dashboards shared together as one"
    ),
    "collection.dashboards.add": "add one more board to an existing collection",
    "collection.dashboards.remove": "take a dashboard out of a collection",
    "collection.share": "share a set of dashboards with people by email as one collection",
    "collection.members.remove": "stop sharing a collection with a person",
    "collection.for-dashboard": (
        "which collections hold this dashboard groups containing this board"
    ),
    "collection.activity": "who opened the collection and which dashboards inside get opened",
    "collection.files.upload": "upload a file to refresh the data behind a collection",
    "collection.active-job": "resume an interrupted upload to a collection, running now",
    "collection.job": "check the progress of one upload job for a collection by job id",
    "dashboard.attachment-create": "attach a report file to the chat for the agent to read",
    "file.multi-sheet-preview": (
        "preview one sheet of a multi-sheet excel file before making datasets"
    ),
    "file.multi-sheet-extract": (
        "make a dataset from each accepted sheet of a multi-sheet excel file"
    ),
    "workflow.save": "save the unsaved changes on the workflow canvas",
    "workflow.duplicate": "duplicate copy clone a workflow onto other datasets",
    "workflow.save-undo": "undo a workflow save roll back the last save run",
    "workflow.save-cancel-step": "cancel one step of a running workflow save stop a save step",
    "view.export.runs": "export run history past runs of an export rows sent errors when it ran",
    "view.export.rest-fill": "propose REST API export settings from an API docs page url",
    "workspace.user.list": (
        "list users members of the workspace or of one project with --project, their roles "
        "and status, who has access, my role in a project"
    ),
    # What was done to the view and what depends on it; column statistics are
    # ``view data profile``.
    "view.summary": (
        "summary of what a dataview has had done to it and where it goes: pipeline steps "
        "actions exports dashboards dependencies downstream, row and column counts"
    ),
    "workspace.export-hosts.get": "hosts exports may send data to allowed export hosts policy",
    "workspace.export-hosts.set": "restrict or allow the hosts exports may send data to",
    "dashboard.email-updates.list": "email updates on dashboards I subscribe to in the workspace",
    "dashboard.email-updates.get": "email update schedule and subscribers for a dashboard",
    "dashboard.email-updates.set": "set the email update schedule for a dashboard",
    "dashboard.email-updates.me.get": "am I subscribed to email updates for this dashboard",
    "dashboard.email-updates.me.set": "subscribe or unsubscribe me from dashboard email updates",
    "dashboard.email-updates.test": "send a test email update for a dashboard",
    "collection.email-updates.get": "email update schedule and subscribers for a collection",
    "collection.email-updates.set": "set the email update schedule for a collection",
    "collection.email-updates.me.get": "am I subscribed to email updates for this collection",
    "collection.email-updates.me.set": "subscribe or unsubscribe me from collection email updates",
    "collection.email-updates.test": "send a test email update for a collection",
    "dashboard.live-chart.list": "list live charts shareable embeddable chart dashboards",
    "dashboard.live-chart.create": "create a live chart embeddable chart from a figure",
    "dashboard.live-chart.get": "get one live chart embed settings",
    "dashboard.live-chart.audience": "change who can see a live chart audience",
    "dashboard.live-chart.usage": "where a live chart is used embeds placements views",
    "dashboard.live-chart.placement": "record where a live chart is placed",
    "dashboard.oembed": "oembed embed metadata for a dashboard link",
    "workflow.archive": "archive a workflow or bring an archived workflow back",
    "workflow.attach-dataset": "add an existing dataset to a workflow",
    "workflow.resolve-held": "settle a change the workflow save held back",
    "auth.connected-apps.list": (
        "which apps can access my account, the apps I authorised, connected apps"
    ),
    "auth.connected-apps.revoke": "disconnect an app I authorised, cut off the app access to me",
    "workspace.current": (
        "which workspace this token acts in, the current workspace, the server fenced to"
    ),
    "workspace.oauth-client.list": (
        "the OAuth clients of this workspace, apps with sign in for users"
    ),
    "workspace.oauth-client.create": (
        "register an OAuth client, a new app for user sign in with Mammoth"
    ),
    "workspace.oauth-client.delete": "delete an OAuth client, the app for user sign in",
    "workspace.oauth-client.revoke-grant": (
        "revoke every grant of an OAuth client make users authorise anew"
    ),
    "dashboard.columns": "columns of the dashboard source data profile samples ranges data panel",
    "dashboard.context.review": "preview what the context change would do to the dashboard dry run",
    "dashboard.context.apply": "apply the reviewed context change to the dashboard",
    "dashboard.qa.insights": "what questions viewers asked on the dashboard grouped unanswered",
    "view.impact": "what breaks if I delete this dataview or a task dependents impact",
    "view.analyze": "which pipeline steps are wasted duplicate suspended no-op filter move earlier",
    "view.optimize": "drop wasted pipeline steps hoist filters",
    "view.compare": "are these two views the same data row counts column differences checksums",
    "dashboard.pbix-intent": "read an attached Power BI workbook against my view what would map",
    "dashboard.pbix-assess": "what does an attached Power BI workbook hold",
    "project.copy": "copy a whole project into a new one datasets views pipelines dashboards",
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
    "support.billing.start-trial": "platform admin begin a free trial days on a workspace",
    "support.billing.end-trial": "platform admin end a workspace trial now charge the plan",
    "support.billing.retry-payment": "platform admin retry a failed payment past due workspace",
    "support.billing.refund": "platform admin refund the last payment of a workspace money back",
    "support.billing.change-plan": (
        "platform admin move a workspace to another plan upgrade downgrade"
    ),
    "support.billing.cancel-subscription": (
        "platform admin cancel a workspace subscription now or at period end"
    ),
    "support.connector.bucket-impact": (
        "platform admin which plans a connector bucket change reaches"
    ),
    "support.entitlement.registry": "platform admin every entitlement key a plan or deal can set",
    "support.plan.catalog": "platform admin plans catalog entitlement values per plan",
    "support.deal.list": "platform admin all deals customer contracts",
    "support.deal.get": "platform admin one deal terms status",
    "support.deal.create": "platform admin new deal contract for a workspace price plan",
    "support.deal.update": "platform admin change deal terms price status contract dates",
    "support.deal.activity": "platform admin deal history audit log",
    "support.deal.move-to-partner": "platform admin move a direct deal under a reseller partner",
    "support.deal.cancel-move-to-partner": "platform admin cancel a pending deal move to a partner",
    "support.deal.opt-in": "platform admin release opt-in rollout pins on a deal",
    "support.deal.preview-entitlement": "platform admin preview what a deal grants entitlements",
    "support.identity.list": "platform admin all users identities across workspaces search",
    "support.identity.get": "platform admin one user identity workspaces memberships",
    "support.partner.list": "platform admin all partners resellers",
    "support.partner.get": "platform admin one partner contact billing terms",
    "support.partner.create": "platform admin new partner reseller",
    "support.partner.update": "platform admin change partner contact billing method notes status",
    "support.partner.activity": "platform admin partner history audit log",
    "support.partner.billing": "platform admin partner billing summary balance",
    "support.partner.invoices": "platform admin partner invoices open paid",
    "support.partner.charge-invoices": "platform admin charge a partner open invoices now",
    "support.partner.send-payment-link": "platform admin email a partner a payment link",
    "support.partner.client.list": "platform admin a partner client workspaces",
    "support.partner.client.delete": "platform admin remove a partner client workspace",
    "support.partner.client.detach": "platform admin detach a partner client into a direct deal",
    "support.partner.client.cancel-detach": "platform admin cancel a pending client detach",
    "support.search": "platform admin command palette find workspace partner user by text",
    "support.triage": "platform admin attention queue failed payments expiring trials",
    "support.usage-tiles": "platform admin usage overview tiles totals",
    "support.workspace.activity": "platform admin workspace history audit log",
    "support.workspace.entitlement": "platform admin what a workspace entitlements resolve to",
    "support.workspace.deal-seed": "platform admin deal terms a workspace subscription would seed",
    "support.workspace.chargebee-cancelled": (
        "platform admin mark a workspace cancelled in chargebee"
    ),
    "support.workspace.archive-info": (
        "platform admin what archiving a workspace does archive state"
    ),
    "support.workspace.archive": "platform admin archive a workspace to cold storage glacier",
    "support.workspace.restore-archive": (
        "platform admin restore an archived workspace from cold storage"
    ),
    "support.workspace.invite.cancel": "platform admin cancel a pending workspace invite",
    "support.workspace.invite.resend": "platform admin resend a pending workspace invite email",
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
    "file.update": (
        "pdf extraction method choose select pending tables only all content custom "
        "uploaded pdf file extract_pdf_tables"
    ),
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
        "url web link fetch retrieve pull import public website endpoint api json data weburl "
        "file csv from an SFTP server folder cloud storage connection connector as a new dataset "
        "REST API Elasticsearch generic_rest_api on a schedule refresh recurring "
        "database query SQL select table Postgres MySQL SQL Server rest api connector"
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
    "view.derivative.create": (
        "metric kpi number single value to check track daily monitor add a metric "
        "sum of column explore panel card metric card"
    ),
    "view.draft.auto-run": (
        "stop prevent re-running rerun automatically when source changes auto run enable disable"
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
    # From URL: a dataset made from a web link (CSV, Excel or JSON file).
    "dataset.from-url.preview": (
        "preview a URL link before importing, see the columns and first rows of a CSV Excel "
        "or JSON file at a web address, from url, nothing is kept"
    ),
    "dataset.from-url.follow": (
        "follow link, stop following a link, make a dataset a copy, refresh from URL again, "
        "keep a url dataset updated from its link"
    ),
    "dataset.from-url.links": (
        "which url link datasets follow a link, last fetched, fetch failed, "
        "refresh from link schedules, which links update"
    ),
    # Bulk download (several datasets, views or folders as one file).
    "dataset.download": (
        "download all datasets as zip, export several datasets to one file, bulk download "
        "many tables CSV zip of CSVs or one Excel xlsx workbook with a sheet per dataset, "
        "stack same columns, save to computer"
    ),
    "dataset.download-plan": (
        "how big is a bulk download, how many datasets and files a download of several "
        "datasets would hold before downloading all as zip, stacked files, skipped empty"
    ),
    # Move a project to another workspace (tech admin).
    "support.workspace.project.list": (
        "list a workspace's projects and which have a move to another workspace unfinished"
    ),
    "support.workspace.project.move-check": (
        "check move project to another workspace, blockers and warnings before the move"
    ),
    "support.workspace.project.move-start": (
        "move project to another workspace, transfer a project, resume a stalled project move"
    ),
    "support.project-move.get": (
        "project move status progress error stalled, is the move to another workspace done"
    ),
    "support.project-move.purge": (
        "purge delete the source copies left in the old workspace after a project move"
    ),
    "batch.delete": (
        "undo the file just appended take back an append revert remove roll back the last upload "
        "batch of data added to a dataset delete a batch"
    ),
    "file.extract-sheets": (
        "second tab tabs of a workbook pull chosen tabs out of an xlsx file into datasets"
    ),
    "dataset.update-method.set": (
        "replace overwrite a dataset's data with a newer file or append instead update method "
        "mode refresh data"
    ),
    "dataset.file-settings.update": (
        "skip title rows header rows at the top change the delimiter separator quote character "
        "of an uploaded csv file parsing settings"
    ),
    # The project workflow-template catalog (ready-made reconciliations and reports). The legacy
    # workspace `template` group is a different, older API and says so.
    "workflow.template.list": (
        "list browse search the workflow template catalog, ready-made workflows to start from, "
        "bank reconciliation three-way match payroll vendor statement intercompany inventory "
        "reconciliation, which workflow templates exist"
    ),
    "workflow.template.get": (
        "one workflow template's inputs roles settings, what tables and columns a catalog "
        "template needs before you build it"
    ),
    "workflow.template.sample-result": (
        "see what a workflow template produces on its own sample rows without importing or "
        "building anything, example result of a catalog template"
    ),
    "workflow.template.rank": (
        "which of my tables fit a workflow template input, find the dataset for a template, "
        "rank datasets by how well their columns match"
    ),
    "workflow.template.fit": (
        "match a workflow template's roles to my columns, which column plays each role, "
        "map columns for a catalog template"
    ),
    "workflow.template.preview": (
        "preview a workflow template on my rows before building, try a catalog template, "
        "check its result and checks without saving"
    ),
    "workflow.template.samples": (
        "import a workflow template's sample tables into the project to try the template "
        "without my own data"
    ),
    "workflow.template.build": (
        "build a workflow from a catalog template, use a workflow template on my tables, "
        "create the reconciliation workflow and its result table"
    ),
    "template.list": (
        "legacy workspace templates (older API), not the workflow template catalog; for "
        "ready-made workflows use workflow template list"
    ),
}
