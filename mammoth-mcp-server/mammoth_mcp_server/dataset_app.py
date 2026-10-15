"""Preview a query on a database connection, with the form that makes it a dataset.

Making a dataset from a query takes three choices: the query, how often to pull
it, and what a refresh does with the rows. Asked one by one in the chat, that
is three round trips. `preview_query` names a `ui://` page instead, and a host
with MCP Apps draws it under the call: the first rows, with the name, the
query, the schedule and the refresh already filled in. One button makes the
dataset (`add_dataset_from_connection`) and puts a turn in the chat
(`ui/message`), so the model carries on.

A client without MCP Apps shows the rows, and the model asks once, with the
defaults filled in.

Like `upload_app`, this module imports nothing from `server`.
"""

import json
import re
from string import Template

from mcp.server.mcpserver.exceptions import ToolError

from .chat_apps import chat_apps
from .consts import DATASET_APP_URI, ConnectionFields
from .sdk import JsonValue, build_client, read_sdk_errors
from .tool_kinds import DESTRUCTIVE

NOT_A_DATABASE = (
    "Only a database connection can be read from here. For this source, use"
    " `connect_source`: the user picks the data in Mammoth."
)
NOT_A_READ = (
    "Send one query that reads: it must start with SELECT or WITH, be one"
    " statement, and not name INSERT, UPDATE, DELETE, CREATE, DROP or another"
    ' word that writes. A column with such a name can be quoted, as "merge".'
)
UNREADABLE = (
    "Send the query without backslashes, $$ quotes, # comments and /*! */"
    " comments: some databases read them in a way the check cannot follow."
)

# `$fields` is filled by `render_app`; the script uses no `$` of its own.
DATASET_APP = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    :root { color-scheme: light dark; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
           sans-serif; margin: 0; padding: 12px; font-size: .9rem; }
    .rows { overflow-x: auto; max-height: 220px; margin-bottom: 12px; }
    table { border-collapse: collapse; font-size: .8rem; }
    th, td { border: 1px solid #9aa5b1; padding: 3px 6px; text-align: left;
             white-space: nowrap; }
    label { display: block; margin: 8px 0 3px; font-weight: 600; }
    input, textarea, select { font: inherit; box-sizing: border-box; }
    input[type=text], textarea { width: 100%; }
    textarea { min-height: 64px; font-family: ui-monospace, monospace; }
    input[type=number] { width: 64px; }
    .line { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
    button { margin-top: 12px; font: inherit; font-weight: 600; padding: 9px 16px;
             border: 0; border-radius: 8px; background: #2563eb; color: #fff;
             cursor: pointer; }
    button:disabled { opacity: .5; cursor: default; }
    #state { margin-top: 10px; min-height: 1.2rem; }
    #state.failed { color: #b91c1c; }
  </style>
</head>
<body>
  <div class="rows"><table id="rows"></table></div>
  <label for="name">Dataset name</label>
  <input id="name" type="text">
  <label for="query">Query</label>
  <textarea id="query"></textarea>
  <label for="repeat">Pull</label>
  <div class="line">
    <select id="repeat">
      <option value="once" selected>Once, now</option>
      <option value="hourly">Every … hours</option>
      <option value="daily">Every … days</option>
      <option value="weekly">Every … weeks</option>
      <option value="monthly">Every … months</option>
    </select>
    <span id="everyBox" hidden>every <input id="every" type="number" min="1" value="1"></span>
  </div>
  <label for="refresh">On each refresh</label>
  <select id="refresh">
    <option value="replace" selected>Replace the rows</option>
    <option value="append">Add the new rows</option>
  </select>
  <br><button id="go" disabled>Create dataset</button>
  <div id="state"></div>
<script>
const FIELDS = $fields;
const $$ = id => document.getElementById(id);
const pending = new Map();
let nextId = 1;
let source = null;

function post(message) {
  window.parent.postMessage(Object.assign({ jsonrpc: "2.0" }, message), "*");
}

function ask(method, params) {
  const id = nextId++;
  post({ id: id, method: method, params: params });
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

function resize() {
  post({
    method: "ui/notifications/size-changed",
    params: { width: document.body.scrollWidth, height: document.body.scrollHeight },
  });
}

function say(kind, text) {
  $$("state").className = kind;
  $$("state").textContent = text;
  resize();
}

window.addEventListener("message", event => {
  if (event.source !== window.parent) return;
  const message = event.data || {};
  if (message.method === "ui/notifications/tool-result") {
    takePreview(message.params || {});
  } else if (!message.method && pending.has(message.id)) {
    const waiter = pending.get(message.id);
    pending.delete(message.id);
    message.error ? waiter.reject(message.error) : waiter.resolve(message.result);
  }
});

function drawRows(columns, rows) {
  const table = $$("rows");
  const head = table.insertRow();
  columns.forEach(name => {
    const cell = document.createElement("th");
    cell.textContent = name;
    head.appendChild(cell);
  });
  rows.forEach(row => {
    const line = table.insertRow();
    columns.forEach(name => { line.insertCell().textContent = String(row[name] ?? ""); });
  });
}

function takePreview(result) {
  const found = result.structuredContent || {};
  source = found[FIELDS.source] || null;
  drawRows(found[FIELDS.columns] || [], found[FIELDS.rows] || []);
  if (!source) {
    say("failed", "This preview came with nothing to make a dataset from.");
    return;
  }
  $$("name").value = source[FIELDS.name] || "";
  $$("query").value = source[FIELDS.query] || "";
  $$("go").disabled = false;
  resize();
}

$$("repeat").addEventListener("change", () => {
  $$("everyBox").hidden = $$("repeat").value === "once";
  resize();
});

$$("go").addEventListener("click", async () => {
  const name = $$("name").value.trim();
  if (!name) return say("failed", "Give the dataset a name.");
  $$("go").disabled = true;
  say("", "Creating the dataset…");
  const choices = {
    [FIELDS.name]: name,
    [FIELDS.query]: $$("query").value,
    [FIELDS.repeat]: $$("repeat").value,
    [FIELDS.every]: Number($$("every").value) || 1,
    [FIELDS.onRefresh]: $$("refresh").value,
  };
  let result;
  try {
    result = await ask("tools/call", {
      name: "add_dataset_from_connection",
      arguments: Object.assign({}, source, choices),
    });
  } catch (failed) {
    $$("go").disabled = false;
    return say("failed", "Mammoth did not take it. Ask the assistant to try again.");
  }
  const made = (result && result.structuredContent) || {};
  if (!result || result.isError) {
    $$("go").disabled = false;
    const text = ((result || {}).content || []).map(part => part.text || "").join(" ");
    return say("failed", text || "Mammoth did not take it.");
  }
  const turn = "I created the dataset " + name + " from that query (" +
    made[FIELDS.schedule] + "). Carry on with it.";
  try {
    await ask("ui/message", { role: "user", content: [{ type: "text", text: turn }] });
    say("", "Created. The conversation carries on.");
  } catch (refused) {
    say("", "Created. Tell the assistant it is done.");
  }
});

ask("ui/initialize", {
  appInfo: { name: "mammoth-dataset", version: "1.0.0" },
  appCapabilities: {},
  protocolVersion: "2026-01-26",
}).then(() => {
  post({ method: "ui/notifications/initialized", params: {} });
  resize();
});
</script>
</body>
</html>
""")


def render_app() -> str:
    """Draw the form, with the names it shares with the server filled in."""
    fields = {
        "source": ConnectionFields.SOURCE,
        "columns": ConnectionFields.COLUMNS,
        "rows": ConnectionFields.ROWS,
        "name": ConnectionFields.NAME,
        "query": ConnectionFields.QUERY,
        "repeat": ConnectionFields.REPEAT,
        "every": ConnectionFields.EVERY,
        "onRefresh": ConnectionFields.ON_REFRESH,
        "schedule": ConnectionFields.SCHEDULE,
    }
    return DATASET_APP.substitute(fields=json.dumps(fields))


chat_apps.add_html_resource(
    DATASET_APP_URI,
    render_app(),
    name="Mammoth dataset",
    description="Preview a query on a database connection, and make it a dataset.",
)


@chat_apps.tool(resource_uri=DATASET_APP_URI, title="Preview a query", annotations=DESTRUCTIVE)
async def preview_query(
    workspace_id: int,
    project_id: int,
    connector_key: str,
    connection_key: str,
    query: str,
    name: str | None = None,
) -> dict[str, JsonValue]:
    """Run a query on a database connection and show its first rows. Nothing is saved.

    Use it before `add_dataset_from_connection`. Ask the user first: the query
    runs on their own database. Show it to them.

    Many clients draw a form under this call, with the query, the name, the
    schedule and the refresh filled in, and a button that makes the dataset.
    Tell the user to check it and press Create: the form tells you when the
    dataset is made. If none shows, ask about all three in one message, with
    the defaults filled in (pull once, now; a refresh replaces the rows), and
    skip what the user already said. Never ask one by one.

    Args:
        workspace_id: Which workspace the project is in.
        project_id: Which project.
        connector_key: The database's `name_key`, such as "postgres".
        connection_key: What `list_connections` returned.
        query: One SQL query that reads.
        name: The dataset name to suggest in the form, such as the table's.

    Returns:
        `columns` and the first `rows`. `source`: what the form makes the dataset from.
    """
    check_query(connector_key, query)
    async with build_client(workspace_id, project_id) as client:
        answer = await read_sdk_errors(
            client.connectors.query_connection(
                connector_key,
                connection_key,
                query,
                project_id=project_id,
                timeout=ConnectionFields.PREVIEW_SECONDS,
            )
        )
    shaped = shape_sample(answer.get(ConnectionFields.SAMPLE))
    shaped[ConnectionFields.SOURCE] = {
        ConnectionFields.WORKSPACE_ID: workspace_id,
        ConnectionFields.PROJECT_ID: project_id,
        ConnectionFields.CONNECTOR_KEY: connector_key,
        ConnectionFields.CONNECTION_KEY: connection_key,
        ConnectionFields.QUERY: query,
        ConnectionFields.NAME: name,
    }
    return shaped


def check_query(connector_key: str, query: str) -> None:
    """Refuse a source that is not a database, and a query that shows a way to write.

    A query must start with SELECT or WITH, be one statement, and name no
    word that writes, such as DELETE in a CTE or SELECT ... INTO. It is a
    guard, not a parser: a function that writes, such as Postgres's
    `dblink_exec`, still passes, and the connection's database account
    decides what a query may change.
    """
    if connector_key not in ConnectionFields.DATABASES:
        raise ToolError(NOT_A_DATABASE)
    if "\\" in query or ConnectionFields.RUN_COMMENT in query:
        raise ToolError(UNREADABLE)
    if re.search(ConnectionFields.DOLLAR_QUOTE, query):
        raise ToolError(UNREADABLE)
    bare = re.sub(ConnectionFields.QUOTED, " ", query, flags=re.DOTALL).strip().rstrip(";")
    if ConnectionFields.LINE_COMMENT in bare:
        raise ToolError(UNREADABLE)
    words = re.findall(r"\w+", bare.lower())
    if not words or words[0] not in ConnectionFields.READING:
        raise ToolError(NOT_A_READ)
    if ";" in bare or ConnectionFields.WRITES.intersection(words):
        raise ToolError(NOT_A_READ)


def shape_sample(sample: JsonValue) -> dict[str, JsonValue]:
    """The sample's column names and its first rows, each row by column name.

    Mammoth sends the columns under `dataschema` and each row as a list of
    values, in the same order.
    """
    sample = sample if isinstance(sample, dict) else {}
    schema = sample.get(ConnectionFields.SCHEMA)
    rows = sample.get(ConnectionFields.ROWS)
    columns = [
        str(one.get(ConnectionFields.COLUMN_NAME))
        for one in (schema if isinstance(schema, list) else [])
        if isinstance(one, dict)
    ]
    shown: list[JsonValue] = [
        dict(zip(columns, row, strict=False))
        for row in (rows if isinstance(rows, list) else [])[: ConnectionFields.ROWS_SHOWN]
        if isinstance(row, list)
    ]
    return {ConnectionFields.COLUMNS: list[JsonValue](columns), ConnectionFields.ROWS: shown}
