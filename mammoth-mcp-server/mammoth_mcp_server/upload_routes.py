"""The page a user drops a local file on, and the route that takes it.

This is the whole of the upload handoff the user sees: one drop zone, no
pickers and no sign-in. Everything the upload needs was decided when the tool
minted the ticket (`upload_tickets`) — which workspace, which project, and
which user it runs as — so the page asks for nothing but the file.

The bytes go from the browser to this server and on to the same upload route the web
app uses. They never pass through the model, so size and format are Mammoth's
limits rather than a conversation's.
"""

import json
from datetime import UTC, datetime

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from mammoth.exceptions import MammothAPIError, MammothError

from .config import MCP_UPLOAD_URL
from .consts import UPLOAD_FIELD, ApiPaths, ErrorFields, UploadFields
from .jobs import find_job_id
from .sdk import FileUpload, FileUploads, JsonValue, build_client
from .store import Record
from .upload_tickets import as_the_caller, read_caller, read_live_ticket, spend_ticket

UNKNOWN_MEDIA_TYPE = "application/octet-stream"
EXPIRED = "This upload link has expired. Ask for a new one in your conversation."
NO_FILE = "Pick at least one file to upload."
REFUSED = "Mammoth would not take the file."
# What a refusal that carries no status of its own is reported as: the upload
# did reach Mammoth, so this server is relaying an answer, not failing.
RELAYED_STATUS = 502
# The largest file the page takes, which is the upload route's own limit.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

UPLOAD_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mammoth Analytics — Upload</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
           sans-serif; background: #f5f5f5; display: flex; justify-content: center;
           align-items: center; min-height: 100vh; }}
    .card {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.08);
            padding: 2.5rem; width: 100%; max-width: 460px; text-align: center; }}
    h1 {{ font-size: 1.4rem; margin-bottom: .25rem; }}
    p.sub {{ color: #666; font-size: .9rem; margin-bottom: 1.5rem; }}
    #drop {{ border: 2px dashed #cfd8e3; border-radius: 10px; padding: 2.5rem 1rem;
            cursor: pointer; color: #4a5568; font-size: .95rem; }}
    #drop.over {{ border-color: #4a90d9; background: #f0f7fd; }}
    #state {{ margin-top: 1.25rem; font-size: .9rem; color: #4a5568; min-height: 1.2rem; }}
    #state.done {{ color: #15803d; font-weight: 600; }}
    #state.failed {{ color: #b91c1c; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Mammoth Analytics</h1>
    <p class="sub">Choose the files to bring into Mammoth. Any size, any format.</p>
    <div id="drop">Drop files here, or click to choose</div>
    <input id="picker" type="file" multiple hidden>
    <div id="state"></div>
  </div>
<script>
const url = {url};
const drop = document.getElementById("drop");
const picker = document.getElementById("picker");
const state = document.getElementById("state");

drop.onclick = () => picker.click();
drop.ondragover = event => {{ event.preventDefault(); drop.classList.add("over"); }};
drop.ondragleave = () => drop.classList.remove("over");
drop.ondrop = event => {{
  event.preventDefault();
  drop.classList.remove("over");
  send(event.dataTransfer.files);
}};
picker.onchange = () => send(picker.files);

async function send(files) {{
  if (!files.length) return;
  state.className = "";
  state.textContent = "Uploading " + files.length + " file(s)…";
  const body = new FormData();
  for (const file of files) body.append("{field}", file);
  let answer;
  try {{
    answer = await fetch(url, {{ method: "POST", body: body }});
  }} catch (failed) {{
    state.className = "failed";
    state.textContent = "The upload did not reach Mammoth. Try again.";
    return;
  }}
  if (!answer.ok) {{
    state.className = "failed";
    state.textContent = (await answer.json().catch(() => ({{}})))["{message_field}"]
      || "Mammoth refused the upload.";
    return;
  }}
  drop.remove();
  state.className = "done";
  state.textContent = "Uploaded. You can go back to your conversation.";
}}
</script>
</body>
</html>
"""
EXPIRED_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mammoth Analytics — Upload</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
           sans-serif; background: #f5f5f5; display: flex; justify-content: center;
           align-items: center; min-height: 100vh; margin: 0; }}
    .card {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.08);
            padding: 2.5rem; max-width: 420px; text-align: center; }}
    h1 {{ font-size: 1.2rem; margin: 0 0 .5rem; }}
    p {{ color: #666; font-size: .9rem; margin: 0; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>This link is no longer good</h1>
    <p>{message}</p>
  </div>
</body>
</html>
"""


def render_upload(upload_id: str) -> str:
    """Draw the upload page, pointed at the URL the browser can reach.

    The link goes in as a JSON string rather than into the markup, so nothing
    in the ticket can close an attribute or end the script.
    """
    link = json.dumps(f"{MCP_UPLOAD_URL}?{UploadFields.TICKET}={upload_id}")
    return UPLOAD_PAGE.format(url=link, field=UPLOAD_FIELD, message_field=ErrorFields.MESSAGE)


# The in-chat uploader runs in the host's sandboxed frame, on an origin of the
# host's own. The browser hides an answer from another origin unless it says the
# frame may read it. Any origin may: the request carries no cookie, and the
# single-use ticket in its URL is what lets it in.
ANY_ORIGIN = {"Access-Control-Allow-Origin": "*"}


async def upload(request: Request) -> Response:
    """Show the drop zone, or take the files the browser picked."""
    ticket_id = request.query_params.get(UploadFields.TICKET, "")
    if request.method == "GET":
        return await show_upload_page(ticket_id)
    answer = await take_the_upload(request, ticket_id)
    answer.headers.update(ANY_ORIGIN)
    return answer


async def show_upload_page(ticket_id: str) -> Response:
    """Show the drop zone, or say the link is spent."""
    if await read_live_ticket(ticket_id) is None:
        return HTMLResponse(EXPIRED_PAGE.format(message=EXPIRED), status_code=410)
    return HTMLResponse(render_upload(ticket_id))


async def take_the_upload(request: Request, ticket_id: str) -> Response:
    """Send the files to Mammoth as the user who asked for the link.

    Returns:
        The upload's status. The job is left running: `check_upload` reads
        it as the polling user, who is the only one entitled to.
    """
    ticket = await read_live_ticket(ticket_id)
    if ticket is None:
        return JSONResponse({ErrorFields.MESSAGE: EXPIRED}, status_code=410)
    form = await request.form(max_part_size=MAX_UPLOAD_BYTES)
    files = [
        await read_upload(one) for one in form.getlist(UPLOAD_FIELD) if isinstance(one, UploadFile)
    ]
    if not files:
        return JSONResponse({ErrorFields.MESSAGE: NO_FILE}, status_code=400)
    uploaded_at = datetime.now(UTC).isoformat()
    try:
        started = await send_to_mammoth(ticket, files)
    except MammothError as refused:
        # Mammoth's own words: "not authorized", a project pin, a size limit.
        # Unhandled, this leaves as a 500 and the page can only say the upload
        # was refused, which tells the user nothing to act on.
        return JSONResponse(
            {ErrorFields.MESSAGE: str(refused).strip() or REFUSED},
            status_code=refused_status(refused),
        )
    await spend_ticket(
        ticket_id,
        ticket,
        find_job_id(started),
        [name for name, _, _ in files],
        uploaded_at=uploaded_at,
    )
    return JSONResponse({UploadFields.STATUS: UploadFields.PROCESSING})


def refused_status(refused: MammothError) -> int:
    """The status to answer with: Mammoth's own, or a plain relay failure."""
    status = getattr(refused, "status_code", None) if isinstance(refused, MammothAPIError) else None
    return status if isinstance(status, int) and 400 <= status <= 599 else RELAYED_STATUS


async def send_to_mammoth(ticket: Record, files: FileUploads) -> dict[str, JsonValue]:
    """Upload the files to the ticket's project, as the user who asked for it.

    The same route the web app uploads through, so every check, limit and
    audit trail is the user's own.
    """
    workspace_id = int(ticket[UploadFields.WORKSPACE_ID])
    project_id = int(ticket[UploadFields.PROJECT_ID])
    with as_the_caller(read_caller(ticket)):
        async with build_client(workspace_id, project_id) as client:
            # Not `request_api`: that turns a refusal into the ToolError a
            # model reads. This answer goes to a browser, which needs what
            # Mammoth actually said and the status it said it with.
            payload: dict[str, JsonValue] = await client.request_json(
                "POST",
                ApiPaths.FILES.format(workspace_id=workspace_id, project_id=project_id),
                files=[(UPLOAD_FIELD, one) for one in files],
            )
    return payload


async def read_upload(one: UploadFile) -> FileUpload:
    """Read one picked file, as it is sent on to the API."""
    return (
        one.filename or "upload",
        await one.read(),
        one.content_type or UNKNOWN_MEDIA_TYPE,
    )
