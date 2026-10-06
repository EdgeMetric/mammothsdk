"""The uploader drawn in the chat, for a client that speaks MCP Apps.

`request_upload` names a `ui://` page, and a host with MCP Apps renders it in a
sandboxed frame right under the tool call, so the user drops the file without
leaving the conversation. The frame reads the link from the tool result, posts
the files to the same upload route the standalone page uses, and then puts a
turn in the chat itself (`ui/message`), so the model carries on without the
user having to say "done".

A client without MCP Apps ignores the page and shows `upload_url` instead, so
the server does not need to know which kind it is talking to — which, being
stateless, it cannot.

This module imports nothing from `server`: `MCPServer` takes its extensions
when it is built, so this tool has to be bound before the server exists.
"""

import json
from string import Template

from mcp.server.apps import Apps, ResourceCsp
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.mcpserver.exceptions import ToolError

from .config import MCP_UPLOAD_URL, UPLOAD_ORIGIN
from .consts import (
    UPLOAD_APP_URI,
    UPLOAD_FIELD,
    ErrorFields,
    UploadFields,
    UploadReportFields,
)
from .sdk import JsonValue
from .tool_kinds import CHANGES
from .upload_tickets import mint_ticket

upload_app = Apps()

# `$names` are filled by `render_app`; the script uses no `$` of its own.
UPLOAD_APP = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    :root { color-scheme: light dark; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
           sans-serif; margin: 0; padding: 12px; }
    #drop { border: 2px dashed #9aa5b1; border-radius: 10px; padding: 28px 12px;
            text-align: center; cursor: pointer; font-size: .95rem; }
    #drop.over { border-color: #4a90d9; }
    #drop.off { opacity: .5; cursor: default; }
    #state { margin-top: 10px; font-size: .9rem; min-height: 1.2rem; }
    #state.done { color: #15803d; font-weight: 600; }
    #state.failed { color: #b91c1c; }
  </style>
</head>
<body>
  <div id="drop" class="off">Drop files here, or click to choose</div>
  <input id="picker" type="file" multiple hidden>
  <div id="state">Getting the upload link…</div>
<script>
const FIELDS = $fields;
const drop = document.getElementById("drop");
const picker = document.getElementById("picker");
const state = document.getElementById("state");
const pending = new Map();
let nextId = 1;
let upload = null;

function say(kind, text) {
  state.className = kind;
  state.textContent = text;
  resize();
}

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
  if (!found[FIELDS.url]) {
    say("failed", "No upload link came with this call. Ask for a new one.");
    return;
  }
  upload = found;
  drop.classList.remove("off");
  say("", "");
}

drop.onclick = () => upload && picker.click();
drop.ondragover = event => { event.preventDefault(); drop.classList.add("over"); };
drop.ondragleave = () => drop.classList.remove("over");
drop.ondrop = event => {
  event.preventDefault();
  drop.classList.remove("over");
  if (upload) send(event.dataTransfer.files);
};
picker.onchange = () => send(picker.files);

async function send(files) {
  if (!files.length) return;
  say("", "Uploading " + files.length + " file(s)…");
  const body = new FormData();
  for (const file of files) body.append(FIELDS.file, file);
  let answer;
  try {
    answer = await fetch(upload[FIELDS.url], { method: "POST", body: body });
  } catch (failed) {
    say("failed", "The upload did not reach Mammoth. Try again.");
    return;
  }
  if (!answer.ok) {
    const refused = await answer.json().catch(() => ({}));
    say("failed", refused[FIELDS.message] || "Mammoth refused the upload.");
    return;
  }
  drop.remove();
  const names = Array.from(files, file => file.name).join(", ");
  say("", "Uploaded. Mammoth is reading " + names + "…");
  await handBack(names, await waitForMammoth());
}

// Ask the server, through the host, until Mammoth has read the files. A host
// that cannot call tools from here, or an upload still going after ten
// minutes, gets the upload id instead, and the model asks.
async function waitForMammoth() {
  const giveUp = Date.now() + 10 * 60 * 1000;
  while (Date.now() < giveUp) {
    let result;
    try {
      result = await ask("tools/call", {
        name: "check_upload",
        arguments: { [FIELDS.id]: upload[FIELDS.id] },
      });
    } catch (failed) {
      return null;
    }
    const checked = (result && result.structuredContent) || {};
    if (result && result.isError) return null;
    if (checked[FIELDS.status] === FIELDS.done) return checked;
    await new Promise(wake => setTimeout(wake, 3000));
  }
  return null;
}

async function handBack(names, checked) {
  const details = checked
    ? JSON.stringify(checked)
    : "Call check_upload with upload_id " + upload[FIELDS.id] + " to see them.";
  try {
    await ask("ui/update-model-context", {
      content: [{ type: "text", text: "Upload finished. " + details }],
    });
  } catch (ignored) {}
  const waiting = ((checked || {})[FIELDS.files] || []).filter(item => item[FIELDS.needs]);
  const asking = "Ask me about each one, and do not choose for me.";
  const turn = waiting.length
    ? "I uploaded " + names + " to Mammoth. Some of it cannot be finished" +
      " without a decision from me. " + asking
    : "I uploaded " + names + " to Mammoth. Carry on with it.";
  try {
    await ask("ui/message", { role: "user", content: [{ type: "text", text: turn }] });
    say("done", "Done. The conversation carries on.");
  } catch (refused) {
    say("done", "Done. Tell the assistant the files are in.");
  }
}

ask("ui/initialize", {
  appInfo: { name: "mammoth-upload", version: "1.0.0" },
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
    """Draw the uploader, with the names it shares with the server filled in."""
    fields = {
        "url": UploadFields.UPLOAD_URL,
        "id": UploadFields.UPLOAD_ID,
        "status": UploadFields.STATUS,
        "done": UploadFields.DONE,
        "files": UploadFields.FILES,
        "needs": UploadReportFields.NEEDS,
        "file": UPLOAD_FIELD,
        "message": ErrorFields.MESSAGE,
    }
    return UPLOAD_APP.substitute(fields=json.dumps(fields))


upload_app.add_html_resource(
    UPLOAD_APP_URI,
    render_app(),
    name="Mammoth upload",
    description="Drop files from this machine into a Mammoth project.",
    csp=ResourceCsp(connect_domains=[UPLOAD_ORIGIN]),
)


@upload_app.tool(resource_uri=UPLOAD_APP_URI, annotations=CHANGES)
async def request_upload(workspace_id: int, project_id: int) -> dict[str, JsonValue]:
    """Let the user upload files from their own machine.

    Use this for any file you do not already hold as text: a spreadsheet, a
    large CSV, anything binary. The browser sends the file straight to
    Mammoth, so its size and format do not matter and nothing is retyped here.

    Many clients draw an uploader right under this call. Tell the user to drop
    the file there, then end your turn: the uploader posts a message in the
    chat once Mammoth has the files. If no uploader shows, give the user
    `upload_url` to open, and call `check_upload` with `upload_id` once they
    say it is done.

    The link acts as the user, is good for one upload, and expires in half an
    hour. Ask for a new one rather than reusing an old one.

    Args:
        workspace_id: Which workspace the files land in.
        project_id: Which project the files land in.

    Returns:
        `upload_url`: the link to show the user. `upload_id`: what to call
        `check_upload` with.
    """
    caller = get_access_token()
    if caller is None:
        raise ToolError("Sign in again: this call carries no Mammoth user.")
    upload_id = await mint_ticket(caller, workspace_id, project_id)
    return {
        UploadFields.UPLOAD_URL: f"{MCP_UPLOAD_URL}?{UploadFields.TICKET}={upload_id}",
        UploadFields.UPLOAD_ID: upload_id,
    }
