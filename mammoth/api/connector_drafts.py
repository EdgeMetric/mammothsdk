"""Connector drafts API client: build a connector one step at a time, then save it."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from mammoth.exceptions import MammothAPIError, MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

_list = list  # Alias to avoid shadowing by method name

DRAFT_ORIGINS = ("agent", "connections", "modal")
DRAFT_KINDS = ("native", "rest", "custom_code", "url", "webhook")
LIST_STATUSES = ("live", "saved", "all")
SAVE_REFRESH = ("daily", "manual")
#: The server refuses a sample whose base64 text is longer than this.
SAMPLE_MAX_BASE64 = 7_000_000

#: The agent that builds connectors from a draft's chat, as the web app addresses it.
DRAFT_AGENT_KEY = "mammoth_assistant"

ERR_DRAFT_ID_POSITIVE = "`draft_id` must be a positive integer, got {0}."
ERR_CHOICE = "`{0}` must be one of {1}, got {2!r}."
ERR_PATCH_EMPTY = (
    "Pass at least one of `title`, `target_columns`, `sources`, `primary_source_id`, "
    "`joins` or `echo`."
)
ERR_FILL_SOURCE = "Pass exactly one of `file_object_id` or `dataset_id`."
ERR_SAMPLE_TOO_BIG = (
    "The sample file is too big: the server takes at most about 5 MB "
    "({0} base64 characters); keep the header and the first rows."
)
ERR_SAMPLE_FILE = "The sample file {0} is not a readable local file."
ERR_PREVIEW_LIMIT = "`limit` must be between 1 and 100, got {0}."
#: A slug is lower-case letters, digits and ``_`` where the server writes it
#: (``normalise_slug``); a ``/`` would be read as another path segment, so it is refused here.
ERR_SPEC_SLUG = "`connector_slug` must be a name without '/', got {0!r}."
ERR_SPEC_VERSION = "`version` must be a positive integer, got {0}."
#: A 404 with no error code is the router saying the route does not exist; a spec or draft
#: that is missing comes back with a code (``4CDFT004``, ``4CDFT001``).
ERR_SPEC_NOT_SERVED = (
    "This server does not serve the connector spec read yet. It arrives with the next "
    "server release (mvc-service PR 7302)."
)


def _choice(field: str, value: str | None, allowed: tuple[str, ...]) -> None:
    if value is not None and value not in allowed:
        raise MammothValidationError(ERR_CHOICE.format(field, ", ".join(allowed), value))


class ConnectorDraftsAPI:
    """Client for connector drafts: a connector built step by step before it is saved.

    A draft names the sources to read (an API's records, a database's tables, a
    workbook's tabs), the columns wanted (``target_columns``) and how the sources
    join. Saving it makes one dataset per source and joins the others onto the
    main one.

    Access via ``client.connector_drafts``::

        draft = await client.connector_drafts.create(origin="connections", connector_key="hubspot")
        sources = await client.connector_drafts.sources(draft["id"])
        await client.connector_drafts.save(draft["id"], refresh="daily")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _base(self) -> str:
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        return f"/workspaces/{self._client.workspace_id}/projects/{proj}/connector-drafts"

    def _draft(self, draft_id: int) -> str:
        if draft_id <= 0:
            raise MammothValidationError(ERR_DRAFT_ID_POSITIVE.format(draft_id))
        return f"{self._base()}/{draft_id}"

    async def list(self, status: str | None = None) -> dict[str, Any]:
        """List the project's connector drafts, newest first.

        Args:
            status: ``live`` (drafts not saved yet, the server's default), ``saved``
                or ``all``.

        Returns:
            Dict with ``drafts``.
        """
        _choice("status", status, LIST_STATUSES)
        return await self._client._request_json(
            "GET", self._base(), params={"status": status} if status else None
        )

    async def create(
        self,
        origin: str = "connections",
        *,
        connector_key: str | None = None,
        connection_key: str | None = None,
        kind: str | None = None,
        url: str | None = None,
        request_text: str | None = None,
        title: str | None = None,
        session_id: str | None = None,
        start: bool = True,
    ) -> dict[str, Any]:
        """Start an AI connector draft and send its request as the builder's first turn.

        Without ``session_id`` the server starts a new agent chat for the draft. A
        draft with no ``connection_key`` needs the project admin role. When another
        live draft exists for the same connector or connection, the answer carries
        it as ``resume_candidate``.

        The server only stores ``request_text``; nothing runs until a turn is sent with
        the draft in its ``client_context``. As the web app does, this sends the request
        as that first turn (a ``kind="url"`` draft is read, not chatted, and sends none).
        Follow the turn with ``mammoth agent session messages SESSION_ID``.

        Args:
            origin: Where the draft was started: ``agent``, ``connections`` or ``modal``.
            connector_key: Connector to build on (e.g. ``hubspot``).
            connection_key: An existing connection of that connector.
            kind: ``native``, ``rest``, ``custom_code``, ``url`` or ``webhook``; the
                server picks one from the other fields when omitted.
            url: A web address to read data from.
            request_text: What the user asked for, in their words.
            title: The draft's title.
            session_id: An agent chat to attach the draft to.
            start: Send ``request_text`` as the first agent turn. ``False`` only stores it.

        Returns:
            The new draft. When the first turn was sent it also carries ``first_turn``
            (``session_id``, ``turn_id``, ``request_key``) and ``next``, the command that
            reads the agent's answer. A refused first turn leaves the draft and carries
            ``first_turn_error`` with ``next`` for sending it again.
        """
        _choice("origin", origin, DRAFT_ORIGINS)
        _choice("kind", kind, DRAFT_KINDS)
        body: dict[str, Any] = {"origin": origin}
        for field, value in (
            ("connector_key", connector_key),
            ("connection_key", connection_key),
            ("kind", kind),
            ("url", url),
            ("request_text", request_text),
            ("title", title),
            ("session_id", session_id),
        ):
            if value is not None:
                body[field] = value
        draft = await self._client._request_json("POST", self._base(), json=body)
        if start and request_text and draft.get("kind") != "url" and draft.get("session_id"):
            draft = await self._send_first_turn(draft, request_text)
        return draft

    async def _send_first_turn(self, draft: dict[str, Any], request_text: str) -> dict[str, Any]:
        """Send *request_text* as the draft chat's first turn, keeping the draft on a refusal.

        Args:
            draft: The draft the server just made (``id``, ``session_id``).
            request_text: The user's request.

        Returns:
            *draft* with ``first_turn`` and ``next``, or ``first_turn_error`` and ``next``.
        """
        session_id = draft["session_id"]
        try:
            started = await self._client.agents.chat(
                request_text,
                {"type": "workspace", "workspace_id": await self._client.resolve_workspace_id()},
                agent_key=DRAFT_AGENT_KEY,
                session_id=session_id,
                client_context={"connector_draft": {"id": draft["id"]}},
            )
        except MammothAPIError as error:
            retry = f"mammoth connector draft get {draft['id']}"
            return {**draft, "first_turn_error": str(error), "next": retry}
        return {
            **draft,
            "first_turn": started,
            "next": f"mammoth agent session messages {session_id}",
        }

    async def known_sources(self) -> dict[str, Any]:
        """List the sources with no built-in connector that a draft can still start on.

        Returns:
            Dict with ``sources`` (``key``, ``name``, ``category``, ``tier``,
            ``domain``), deep ones first.
        """
        return await self._client._request_json("GET", f"{self._base()}/known-sources")

    async def link_preview(self, url: str) -> dict[str, Any]:
        """Read the CSV, Excel or JSON file at a link and show its tables, keeping nothing.

        This is the New dataset window's From URL step; it needs no draft.

        Args:
            url: The link to the file (at most 2000 characters).

        Returns:
            Dict with ``tables``: one for a text or JSON file, one per tab for a workbook,
            each ``{name, columns, row_count, has_more, sample_rows}``.
        """
        return await self._client._request_json(
            "POST", f"{self._base()}/link-preview", json={"url": url}
        )

    async def _read_spec(self, path: str) -> dict[str, Any]:
        try:
            return await self._client._request_json("GET", path)
        except MammothAPIError as exc:
            body = exc.response_body if isinstance(exc.response_body, dict) else {}
            if exc.status_code == 404 and not body.get("error_code"):
                raise MammothAPIError(
                    ERR_SPEC_NOT_SERVED,
                    status_code=404,
                    response_body=body,
                    method="GET",
                    operation_state="failed",
                ) from exc
            raise

    async def spec(self, draft_id: int) -> dict[str, Any]:
        """Read the spec an AI-built connector's draft is building, with secrets left out.

        The spec says how each table is read: its request path, where its records sit in
        the response and how pages are requested. A credential shows as a reference to
        the field the sign-in form collected; anything that could be a secret reads
        ``[redacted]``.

        Args:
            draft_id: ID of the draft.

        Returns:
            Dict with ``code_id``, ``connector_slug``, ``version``, ``status``,
            ``is_active``, ``entrypoint``, ``spec_sha256``, ``allowed_hosts``,
            ``created_at`` (ISO 8601), ``tables`` (each
            ``{name, request_path, records_path, paging}``) and the whole ``spec``.
            A literal that could be a secret, and a raw body's ``template`` or an
            XML-RPC body's ``args``, read ``[redacted]``.

        Raises:
            MammothAPIError: 404 when the draft is not in the project or has no AI-built
                connector yet, or when the server does not serve the read yet.
        """
        return await self._read_spec(f"{self._draft(draft_id)}/spec")

    async def version_spec(self, connector_slug: str, version: int) -> dict[str, Any]:
        """Read one stored version of the workspace's AI-built connector, secrets left out.

        Args:
            connector_slug: The connector's slug (the draft spec's ``connector_slug``).
            version: The version number.

        Returns:
            The same dict as :meth:`spec`.

        Raises:
            MammothValidationError: ``connector_slug`` is empty or holds a ``/``, or
                ``version`` is below 1.
            MammothAPIError: 404 when the workspace has no such version, or when the
                server does not serve the read yet.
        """
        if not connector_slug.strip() or "/" in connector_slug:
            raise MammothValidationError(ERR_SPEC_SLUG.format(connector_slug))
        if version <= 0:
            raise MammothValidationError(ERR_SPEC_VERSION.format(version))
        slug = quote(connector_slug, safe="")
        return await self._read_spec(f"{self._base()}/versions/{slug}/{version}/spec")

    async def get(self, draft_id: int) -> dict[str, Any]:
        """Get one draft, with its target columns, sources and thread.

        Args:
            draft_id: ID of the draft.
        """
        return await self._client._request_json("GET", self._draft(draft_id))

    async def update(
        self,
        draft_id: int,
        *,
        title: str | None = None,
        target_columns: _list[dict[str, Any]] | None = None,
        sources: _list[dict[str, Any]] | None = None,
        primary_source_id: str | None = None,
        joins: _list[dict[str, Any]] | None = None,
        echo: str | None = None,
    ) -> dict[str, Any]:
        """Change a draft.

        Args:
            draft_id: ID of the draft.
            title: New title.
            target_columns: The columns wanted, replaced whole; each has ``name``
                and optionally ``source`` (where it comes from) or ``gap``.
            sources: Column picks by source: ``[{"id": ..., "columns": [...]}]``.
            primary_source_id: The source the others join onto.
            joins: How each other source joins the main one:
                ``[{"id": SOURCE_ID, "on": [{"left": COL, "right": COL}]}]``.
            echo: A quiet note added to the draft's thread for the agent's next turn.

        Returns:
            The changed draft.
        """
        body = {
            field: value
            for field, value in (
                ("title", title),
                ("target_columns", target_columns),
                ("sources", sources),
                ("primary_source_id", primary_source_id),
                ("joins", joins),
                ("echo", echo),
            )
            if value is not None
        }
        if not body:
            raise MammothValidationError(ERR_PATCH_EMPTY)
        return await self._client._request_json("PATCH", self._draft(draft_id), json=body)

    async def discard(self, draft_id: int) -> dict[str, Any]:
        """Hide a draft from every list; its chat thread stays.

        Args:
            draft_id: ID of the draft.
        """
        await self._client._request_json("DELETE", self._draft(draft_id))
        return {"draft_id": draft_id, "discarded": True}

    async def sources(self, draft_id: int) -> dict[str, Any]:
        """List a draft's sources.

        The tables its connection lists are added as untested sources; an
        AI-built connector's records source carries its verified columns.

        Args:
            draft_id: ID of the draft.

        Returns:
            Dict with ``sources``.
        """
        return await self._client._request_json("GET", f"{self._draft(draft_id)}/sources")

    async def preview_source(
        self, draft_id: int, source_id: str, limit: int | None = None
    ) -> dict[str, Any]:
        """Read up to ``limit`` rows of one source through its connection.

        What it returned (columns, rows, status) is recorded on the source.

        Args:
            draft_id: ID of the draft.
            source_id: ID of the source (from :meth:`sources`).
            limit: Rows to read, 1-100.

        Returns:
            Dict with ``columns``, ``rows`` and ``row_count``.
        """
        if limit is not None and not 1 <= limit <= 100:
            raise MammothValidationError(ERR_PREVIEW_LIMIT.format(limit))
        return await self._client._request_json(
            "POST",
            f"{self._draft(draft_id)}/sources/{source_id}/preview",
            json={"limit": limit} if limit is not None else {},
        )

    async def join_candidates(self, draft_id: int, source_id: str) -> dict[str, Any]:
        """List the column pairs that could join a source onto the main one.

        The key in use comes first; each pair says how many of the main source's
        rows read so far find a match (an estimate until the save's join runs).

        Args:
            draft_id: ID of the draft.
            source_id: ID of the source to join.

        Returns:
            Dict with ``candidates`` and ``estimated``.
        """
        return await self._client._request_json(
            "GET", f"{self._draft(draft_id)}/sources/{source_id}/join-candidates"
        )

    async def fill(
        self,
        draft_id: int,
        column: str,
        *,
        file_object_id: int | None = None,
        dataset_id: int | None = None,
        key_columns: _list[str] | None = None,
    ) -> dict[str, Any]:
        """Fill one target column by joining an uploaded file or a dataset onto the main source.

        Args:
            draft_id: ID of the draft.
            column: The target column to fill.
            file_object_id: An uploaded file to join.
            dataset_id: A dataset to join.
            key_columns: The columns to join on; the server picks them when omitted.

        Returns:
            Dict with the keys rows match ``on``, ``matched`` and ``total`` (an
            estimate over the preview rows) and an ``unmatched_sample``.

        Raises:
            MammothAPIError: 409 while the file is still being read.
        """
        if (file_object_id is None) == (dataset_id is None):
            raise MammothValidationError(ERR_FILL_SOURCE)
        body: dict[str, Any] = {"column": column}
        if file_object_id is not None:
            body["file_object_id"] = file_object_id
        if dataset_id is not None:
            body["dataset_id"] = dataset_id
        if key_columns is not None:
            body["key_columns"] = key_columns
        return await self._client._request_json("POST", f"{self._draft(draft_id)}/fill", json=body)

    async def sample(self, draft_id: int, path: str | Path) -> dict[str, Any]:
        """Shape the draft's table from a sample CSV, TSV or Excel file.

        The server reads the file's headers and first rows, sets the target
        columns to them, links each to a field of a source it was found in (by
        name or by matching values; a gap where none) and tries any source left
        unread. The file is not kept.

        Args:
            draft_id: ID of the draft.
            path: The sample file.

        Returns:
            Dict with ``columns`` (each with what it matched) and ``tried``.

        Raises:
            MammothValidationError: If *path* is not a file, or is too big.
        """
        file = Path(path)
        if not file.is_file():
            raise MammothValidationError(ERR_SAMPLE_FILE.format(path))
        content = base64.b64encode(file.read_bytes()).decode("ascii")
        if len(content) > SAMPLE_MAX_BASE64:
            raise MammothValidationError(ERR_SAMPLE_TOO_BIG.format(SAMPLE_MAX_BASE64))
        return await self._client._request_json(
            "POST",
            f"{self._draft(draft_id)}/sample",
            json={"file_name": file.name, "content_base64": content},
        )

    async def browse(self, draft_id: int, folder: str | None = None) -> dict[str, Any]:
        """List a folder of a files-shaped source (the top when ``folder`` is omitted).

        For Google Sheets, lists the account's most recent spreadsheets.

        Args:
            draft_id: ID of the draft.
            folder: The folder to list, as an earlier answer's entry ``ref``.

        Returns:
            Dict with ``folder``, ``entries`` (``kind``, ``name``, ``ref``) and
            ``can_open``.
        """
        return await self._client._request_json(
            "GET", f"{self._draft(draft_id)}/browse", params={"folder": folder} if folder else None
        )

    async def open(self, draft_id: int, ref: str, name: str) -> dict[str, Any]:
        """Open a workbook into the draft: each tab becomes a table of the draft.

        Args:
            draft_id: ID of the draft.
            ref: The workbook's ``ref`` from :meth:`browse`.
            name: The workbook's name, which groups its tabs.

        Returns:
            Dict with the draft's ``sources``.
        """
        return await self._client._request_json(
            "POST", f"{self._draft(draft_id)}/open", json={"ref": ref, "name": name}
        )

    async def read_tables(self, draft_id: int) -> dict[str, Any]:
        """Queue reading again every table not read yet, and every one a try failed on.

        Each shows as not read yet until its answer lands on the draft.

        Args:
            draft_id: ID of the draft.

        Returns:
            Dict with ``queued`` (how many tables).
        """
        return await self._client._request_json("POST", f"{self._draft(draft_id)}/read-tables")

    async def save(
        self,
        draft_id: int,
        refresh: str = "manual",
        *,
        dataset_name: str | None = None,
        folder_resource_id: int | None = None,
    ) -> dict[str, Any]:
        """Start the job that saves a draft.

        The job makes one dataset per source and joins the others onto the main
        one; with ``refresh="daily"`` each API or table source refreshes daily. The
        draft's ``result`` is set when the job is done.

        Args:
            draft_id: ID of the draft.
            refresh: ``daily`` or ``manual``.
            dataset_name: Name of the joined dataset.
            folder_resource_id: Folder to put the datasets in.

        Returns:
            Dict with ``job_id``; follow it with ``client.jobs``.
        """
        _choice("refresh", refresh, SAVE_REFRESH)
        body: dict[str, Any] = {"refresh": refresh}
        if dataset_name is not None:
            body["dataset_name"] = dataset_name
        if folder_resource_id is not None:
            body["folder_resource_id"] = folder_resource_id
        return await self._client._request_json("POST", f"{self._draft(draft_id)}/save", json=body)
