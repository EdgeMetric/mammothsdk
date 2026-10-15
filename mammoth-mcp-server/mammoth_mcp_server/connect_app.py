"""The button drawn in the chat to connect a source, for a client that speaks MCP Apps.

`connect_source` names a `ui://` page, and a host with MCP Apps draws it under
the call: one button that opens the connector in Mammoth, where the user signs
in to the source. A sandboxed frame may not open a window itself, so it asks
the host to (`ui/open-link`), and shows the link to copy when the host will not.
It then keeps calling `find_new_connection` for the whole watch, and puts a turn
in the chat (`ui/message`) once the connection is made, so nobody types "done".

A client without MCP Apps ignores the page and shows `mammoth_url` instead.

Like `upload_app`, this module imports nothing from `server`: `MCPServer` takes
its extensions when it is built, so this tool is bound before the server exists.
"""

import json
from datetime import UTC, datetime
from string import Template
from urllib.parse import urlencode

from mcp.server.mcpserver.exceptions import ToolError

from .chat_apps import chat_apps
from .connection_watch import start_watch
from .consts import CONNECT_APP_URI, MAMMOTH_DATA_URL, ApiPaths, ConnectorFields, ListFields
from .sdk import JsonValue, build_client, read_sdk_errors, request_api
from .telemetry import Events, TelemetryFields, record
from .tool_kinds import READS

# `$fields` is filled by `render_app`; the script uses no `$` of its own.
CONNECT_APP = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    :root { color-scheme: light dark; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
           sans-serif; margin: 0; padding: 12px; }
    button { font: inherit; font-weight: 600; padding: 10px 16px; border: 0;
             border-radius: 8px; background: #2563eb; color: #fff; cursor: pointer; }
    button:disabled { opacity: .5; cursor: default; }
    #state { margin-top: 10px; font-size: .9rem; min-height: 1.2rem; }
    #state a { word-break: break-all; }
  </style>
</head>
<body>
  <button id="go" disabled>Connect in Mammoth</button>
  <div id="state"></div>
  <a id="link" target="_blank" rel="noopener" hidden></a>
<script>
const FIELDS = $fields;
const go = document.getElementById("go");
const state = document.getElementById("state");
const link = document.getElementById("link");
const pending = new Map();
let nextId = 1;
let url = null;

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

function say(text, withLink) {
  state.textContent = text;
  if (withLink) {
    link.href = url;
    link.textContent = url;
    link.hidden = false;
    state.appendChild(document.createElement("br"));
    state.appendChild(link);
  }
  resize();
}

window.addEventListener("message", event => {
  if (event.source !== window.parent) return;
  const message = event.data || {};
  if (message.method === "ui/notifications/tool-result") {
    takeLink(message.params || {});
  } else if (!message.method && pending.has(message.id)) {
    const waiter = pending.get(message.id);
    pending.delete(message.id);
    message.error ? waiter.reject(message.error) : waiter.resolve(message.result);
  }
});

function takeLink(result) {
  const found = result.structuredContent || {};
  url = found[FIELDS.url] || null;
  if (!url) {
    go.hidden = true;
    say("Only a project admin can connect a new source to this project.", false);
    return;
  }
  const name = (found[FIELDS.connector] || {})[FIELDS.name];
  go.textContent = name ? "Connect " + name + " in Mammoth" : "Connect a source in Mammoth";
  go.disabled = false;
  resize();
  if (found[FIELDS.watchId]) watch(found[FIELDS.watchId], name || "the source");
}

// Each call holds up to 20 seconds; the watch itself ends five minutes after the link.
async function watch(watchId, name) {
  while (true) {
    let result;
    try {
      result = await ask("tools/call", {
        name: "find_new_connection",
        arguments: { [FIELDS.watchId]: watchId },
      });
    } catch (failed) {
      return;
    }
    if (!result || result.isError) return;
    const status = (result.structuredContent || {})[FIELDS.status];
    if (status === FIELDS.connected) return carryOn(name);
    if (status !== FIELDS.waiting) {
      say("Not connected yet. Tell the assistant when it is.", false);
      return;
    }
  }
}

async function carryOn(name) {
  go.disabled = true;
  try {
    await ask("ui/message", {
      role: "user",
      content: [{ type: "text", text: "I connected " + name + " in Mammoth. Carry on with it." }],
    });
    say("Connected. The conversation carries on.", false);
  } catch (refused) {
    say("Connected. Tell the assistant it is done.", false);
  }
}

go.addEventListener("click", async () => {
  try {
    await ask("ui/open-link", { url: url });
    say("Mammoth is open in a new tab. Come back here when the data is in.", false);
  } catch (refused) {
    say("Open this link to connect it:", true);
  }
});

ask("ui/initialize", {
  appInfo: { name: "mammoth-connect", version: "1.0.0" },
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
    """Draw the button, with the names it shares with the server filled in."""
    fields = {
        "url": ListFields.MAMMOTH_URL,
        "connector": ConnectorFields.CONNECTOR,
        "name": ConnectorFields.SHOWN_NAME,
        "watchId": ConnectorFields.WATCH_ID,
        "status": ConnectorFields.STATUS,
        "connected": ConnectorFields.CONNECTED,
        "waiting": ConnectorFields.WAITING,
    }
    return CONNECT_APP.substitute(fields=json.dumps(fields))


chat_apps.add_html_resource(
    CONNECT_APP_URI,
    render_app(),
    name="Mammoth connect",
    description="Open a connector in Mammoth, to bring a source's data into a project.",
)

CHECK_THE_KEY = "Check the key with `list_connectors`."
IN_MAMMOTH = (
    "Tell the user to press the button, or give them `mammoth_url`. In Mammoth"
    " they sign in to the source, pick the data to bring in and, if they like,"
    " how often to refresh it. Then"
    " call `find_new_datasets` with `since` at once: it waits while they work."
)
WATCHED = (
    "Tell the user to press the button, or give them `mammoth_url`. In Mammoth"
    " they sign in to the source, which makes a connection; it takes them two or"
    " three minutes. Call `find_new_connection` with `watch_id` at once: it waits"
    " while they work, and reports the connection as soon as it is made."
)
OFF_THE_PLAN = (
    " This connector is not on the workspace's plan: Mammoth offers the upgrade"
    " on that page. Tell the user before they open it."
)
NOT_AN_ADMIN = (
    "Only a project admin can connect a new source to this project, and the user"
    " is not one. Tell them to ask a project admin to connect it, or to make"
    " them one. Data from a database the project already has connected can still"
    " be brought in from here: see `list_connections`."
)


@chat_apps.tool(resource_uri=CONNECT_APP_URI, title="Connect a data source", annotations=READS)
async def connect_source(
    workspace_id: int, project_id: int, connector_key: str | None = None
) -> dict[str, JsonValue]:
    """Give the user the page in Mammoth where they connect a source and bring its data in.

    Nothing is connected here: the user signs in to the source themselves, in
    Mammoth. Use this when the user wants data from a database or an app
    rather than a file; for a file, use `request_upload`. Many clients draw a
    button under this call: tell the user to press it, and if none shows,
    give them `mammoth_url`. When the project
    already has a connection to that database (`list_connections`), bring the
    data in with `add_dataset_from_connection` instead: no link needed.

    Args:
        workspace_id: Which workspace to act in.
        project_id: Which project the data goes into.
        connector_key: The connector's `name_key`, as `list_connectors` lists
            it, such as "postgres" or "hubspot". Omit to let the user pick one.

    Returns:
        `mammoth_url`: the page to give the user. `since`: the time to pass to
        `find_new_datasets` once they are done. `next_step`: what to do now.
        `connector`: its `key` and `name`, and `watch_id`, for
        `find_new_connection`, when one was named. A user who is
        not a project admin gets no link: `next_step` says what they can do.
    """
    if not await may_connect(workspace_id, project_id):
        return {ConnectorFields.NEXT_STEP: NOT_AN_ADMIN}
    handed: dict[str, JsonValue] = {ConnectorFields.SINCE: datetime.now(UTC).isoformat()}
    handed.update(await link_to(workspace_id, project_id, connector_key))
    # The key is checked against Mammoth's connectors, so it is never the user's text.
    record(Events.SOURCE_LINKED, **{TelemetryFields.CONNECTOR: connector_key})
    return handed


async def link_to(
    workspace_id: int, project_id: int, connector_key: str | None
) -> dict[str, JsonValue]:
    """The page that opens the connector, what to do next, and the connector's name."""
    link: dict[str, str] = {ConnectorFields.ACTION: ConnectorFields.ADD_CONNECTOR}
    handed: dict[str, JsonValue] = {ConnectorFields.NEXT_STEP: IN_MAMMOTH}
    if connector_key is not None:
        connector = await read_connector(workspace_id, connector_key)
        link[ConnectorFields.CONNECTOR] = connector_key
        handed[ConnectorFields.CONNECTOR] = {
            ConnectorFields.SHOWN_KEY: connector_key,
            ConnectorFields.SHOWN_NAME: connector.get(ConnectorFields.NAME),
        }
        handed[ConnectorFields.WATCH_ID] = await start_watch(
            workspace_id, project_id, connector_key
        )
        handed[ConnectorFields.NEXT_STEP] = WATCHED
        if connector.get(ConnectorFields.AVAILABLE) is False:
            handed[ConnectorFields.NEXT_STEP] = WATCHED + OFF_THE_PLAN
    link[ConnectorFields.FROM] = ConnectorFields.ASSISTANT
    page = MAMMOTH_DATA_URL.format(workspace_id=workspace_id, project_id=project_id)
    handed[ListFields.MAMMOTH_URL] = f"{page}?{urlencode(link)}"
    return handed


async def may_connect(workspace_id: int, project_id: int) -> bool:
    """Whether the caller is a project admin here, the one role Mammoth lets connect a source."""
    async with build_client(workspace_id) as client:
        me = await request_api(
            client, "GET", ApiPaths.SELF, query={ConnectorFields.FIELDS: ConnectorFields.USER_ROLES}
        )
    roles = me.get(ConnectorFields.USER_ROLES)
    projects = roles.get(ConnectorFields.PROJECTS) if isinstance(roles, dict) else None
    role = projects.get(str(project_id)) if isinstance(projects, dict) else None
    return role == ConnectorFields.CONNECTS


async def read_connector(workspace_id: int, connector_key: str) -> dict[str, JsonValue]:
    """The connector Mammoth has under this key, or a refusal that says where to look."""
    async with build_client(workspace_id) as client:
        try:
            return await read_sdk_errors(client.connectors.get(connector_key))
        except ToolError as refused:
            raise ToolError(f"{refused}. {CHECK_THE_KEY}") from refused
