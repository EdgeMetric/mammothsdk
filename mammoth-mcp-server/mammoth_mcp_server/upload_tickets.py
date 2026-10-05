"""The ticket behind the upload handoff, and the caller it stands for.

A tool argument carries text, so a spreadsheet or a large CSV cannot travel
through the model at all. The browser already holds the one piece of local
filesystem access every client shares — its file picker. So `request_upload`
mints a ticket, hands the user a link that carries it, and the page at that
link sends Mammoth the file.

The browser that opens the page carries no Mammoth login, and asking for one
loses a meaningful share of users. So the ticket stands in for the caller: the
record holds the MCP caller's own access token, sealed with the same key the
sign-in seals credentials with (`store.seal`). It is spent on
the first upload and expires after `UPLOAD_SECONDS`, and the link that carries
it is 256 bits of randomness — the same thing that guards an authorization
code.
"""

import secrets
import typing
from collections.abc import Generator
from contextlib import contextmanager

from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken

from .consts import UPLOAD_SECONDS, UploadFields
from .store import Record, recall, remember, seal, unseal


async def mint_ticket(caller: AccessToken, workspace_id: int, project_id: int) -> str:
    """Remember who is uploading where, and return the ticket that stands for it.

    Args:
        caller: The MCP caller, whose permissions the upload runs with.
        workspace_id: Which workspace the file lands in.
        project_id: Which project the file lands in.

    Returns:
        The upload id, which is both the ticket in the link and what
        `check_upload` is polled with.
    """
    upload_id = secrets.token_urlsafe(32)
    await remember(
        UploadFields.TICKET,
        upload_id,
        {
            UploadFields.WORKSPACE_ID: workspace_id,
            UploadFields.PROJECT_ID: project_id,
            UploadFields.STATUS: UploadFields.WAITING,
            UploadFields.CALLER: seal(caller.model_dump(mode="json")),
        },
        UPLOAD_SECONDS,
    )
    return upload_id


async def read_ticket(upload_id: str) -> Record | None:
    """Read an upload back, or None once the link has expired."""
    return await recall(UploadFields.TICKET, upload_id)


async def read_live_ticket(upload_id: str) -> Record | None:
    """Read a ticket that can still be used, or None once it cannot.

    A spent ticket is kept so `check_upload` can still say what came of it,
    but it no longer holds the caller, so it opens nothing.
    """
    ticket = await read_ticket(upload_id)
    if ticket is None or UploadFields.CALLER not in ticket:
        return None
    return ticket


async def spend_ticket(
    upload_id: str,
    ticket: Record,
    job_id: int,
    file_names: list[str],
    *,
    uploaded_at: str,
) -> None:
    """Note what the user uploaded, and leave the ticket good for nothing else.

    `uploaded_at` is when the files were sent: what the upload made is what the
    project gained since (`upload_report`).

    The caller's token is dropped with the same write: the link has been used,
    so nothing may act as the user through it again.
    """
    await remember(
        UploadFields.TICKET,
        upload_id,
        {
            **{field: value for field, value in ticket.items() if field != UploadFields.CALLER},
            UploadFields.STATUS: UploadFields.PROCESSING,
            UploadFields.JOB_ID: job_id,
            UploadFields.FILE_NAMES: file_names,
            UploadFields.UPLOADED_AT: uploaded_at,
        },
        UPLOAD_SECONDS,
    )


def read_caller(ticket: Record) -> AccessToken:
    """Read back the MCP caller the ticket was minted for."""
    return AccessToken(**unseal(typing.cast(str, ticket[UploadFields.CALLER])))


@contextmanager
def as_the_caller(caller: AccessToken) -> Generator[None]:
    """Run the block as the user who asked for the upload.

    The page has no caller of its own, and a call to the API takes its
    credentials from whoever the MCP request belongs to. So the ticket's token
    is put back where `sdk.build_client` looks for it, and the
    upload runs with that user's permissions and no others.
    """
    reset = auth_context_var.set(AuthenticatedUser(caller))
    try:
        yield
    finally:
        auth_context_var.reset(reset)
