"""Agent definitions API client: workspace-scoped special agents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

ERR_KEY_REQUIRED = "`agent_key` must be a non-empty string, got {0!r}."
ERR_ID_POSITIVE = "`{0}` must be a positive integer, got {1}."
ERR_NOTE_KIND = '`kind` must be "fact" or "scratch", got {0!r}.'

VALID_NOTE_KINDS = frozenset({"fact", "scratch"})


class AgentDefinitionsAPI:
    """Client for the workspace's agent definitions (special agents).

    A definition is addressed by its ``agent_key`` (a slug, unique per workspace).
    Access via ``client.agent_definitions``::

        await client.agent_definitions.create("margin-watch", "Margin watch", charter="...")
        await client.agent_definitions.goldens_run("margin-watch")
        await client.agent_definitions.publish("margin-watch")
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _base(self) -> str:
        return f"/workspaces/{self._client.workspace_id}/agent-definitions"

    def _path(self, agent_key: str, suffix: str = "") -> str:
        if not agent_key:
            raise MammothValidationError(ERR_KEY_REQUIRED.format(agent_key))
        return f"{self._base()}/{agent_key}{suffix}"

    @staticmethod
    def _check_id(name: str, value: int) -> None:
        if value <= 0:
            raise MammothValidationError(ERR_ID_POSITIVE.format(name, value))

    async def list(self, status: str | None = None) -> dict[str, Any]:
        """List the workspace's agent definitions (deleted ones are excluded).

        Args:
            status: Only definitions in this status: ``draft``, ``published`` or ``disabled``.

        Returns:
            Dict with ``result``: the definitions.
        """
        params = {"status": status} if status is not None else None
        return await self._client._request_json("GET", self._base(), params=params)

    async def create(
        self,
        key: str,
        name: str,
        description: str | None = None,
        charter: str | None = None,
        role: str | None = None,
        propose: bool | None = None,
        project_ids: _list[int] | None = None,
        team: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create an agent definition (it starts as a draft).

        Args:
            key: Slug, ``^[a-z][a-z0-9_-]{1,62}$``, unique in the workspace. Built-in
                agent names are reserved.
            name: Display name (1 to 120 characters).
            description: Short description (500 characters at most).
            charter: The agent's method (20000 characters at most).
            role: A built-in role, see :meth:`roles`. The server defaults to the member role.
            propose: Whether the agent proposes changes for approval. The server defaults to true.
            project_ids: Projects the agent may work in.
            team: ``{"agents": [keys], "max_rounds": 1..6}``.

        Returns:
            The created definition.
        """
        body: dict[str, Any] = {"key": key, "name": name}
        body.update(
            _present(
                description=description,
                charter=charter,
                role=role,
                propose=propose,
                project_ids=project_ids,
                team=team,
            )
        )
        return await self._client._request_json("POST", self._base(), json=body)

    async def roles(self) -> dict[str, Any]:
        """List the built-in roles an agent definition can take.

        Returns:
            Dict with ``result``: ``{role, read_only, permissions}`` rows.
        """
        return await self._client._request_json("GET", f"{self._base()}/roles")

    async def get(self, agent_key: str) -> dict[str, Any]:
        """Get one agent definition.

        Args:
            agent_key: Key of the definition.

        Returns:
            The definition.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("GET", self._path(agent_key))

    async def update(
        self,
        agent_key: str,
        name: str | None = None,
        description: str | None = None,
        charter: str | None = None,
        role: str | None = None,
        propose: bool | None = None,
        project_ids: _list[int] | None = None,
        team: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Change an agent definition; only the fields given are sent.

        A new *charter* becomes a new charter version.

        Args:
            agent_key: Key of the definition.
            name: Display name.
            description: Short description.
            charter: The agent's method.
            role: A built-in role, see :meth:`roles`.
            propose: Whether the agent proposes changes for approval.
            project_ids: Projects the agent may work in (replaces the list).
            team: ``{"agents": [keys], "max_rounds": 1..6}`` (replaces the team).

        Returns:
            The updated definition.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        body = _present(
            name=name,
            description=description,
            charter=charter,
            role=role,
            propose=propose,
            project_ids=project_ids,
            team=team,
        )
        return await self._client._request_json("PATCH", self._path(agent_key), json=body)

    async def delete(self, agent_key: str) -> dict[str, Any]:
        """Delete an agent definition. Its key stays reserved in the workspace.

        Args:
            agent_key: Key of the definition.

        Returns:
            Empty dict (the server answers 204).

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("DELETE", self._path(agent_key))

    async def publish(self, agent_key: str) -> dict[str, Any]:
        """Publish an agent definition.

        The server refuses (409 ``proof_run_required``) unless a finished proof run
        exists for the current charter version.

        Args:
            agent_key: Key of the definition.

        Returns:
            The published definition.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("POST", self._path(agent_key, "/publish"))

    async def disable(self, agent_key: str) -> dict[str, Any]:
        """Disable an agent definition.

        Args:
            agent_key: Key of the definition.

        Returns:
            The disabled definition.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("POST", self._path(agent_key, "/disable"))

    async def charter_versions(self, agent_key: str) -> dict[str, Any]:
        """List the last 10 charter versions of a definition, newest first.

        Args:
            agent_key: Key of the definition.

        Returns:
            Dict with ``result``: ``{version, charter, created_by, created_at}`` rows.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("GET", self._path(agent_key, "/charter-versions"))

    async def charter_restore(self, agent_key: str, version: int) -> dict[str, Any]:
        """Restore an older charter version as a new version.

        Args:
            agent_key: Key of the definition.
            version: Version number from :meth:`charter_versions`.

        Returns:
            The definition with the restored charter.

        Raises:
            MammothValidationError: If *agent_key* is empty or *version* is not positive.
        """
        self._check_id("version", version)
        return await self._client._request_json(
            "POST", self._path(agent_key, f"/charter-versions/{version}/restore")
        )

    async def goldens_list(self, agent_key: str) -> dict[str, Any]:
        """List the golden questions of a definition.

        Args:
            agent_key: Key of the definition.

        Returns:
            Dict with ``result``: the goldens with their last verdict.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("GET", self._path(agent_key, "/goldens"))

    async def goldens_add(self, agent_key: str, question: str, expected: str) -> dict[str, Any]:
        """Add a golden question with the answer it must reach (50 goldens at most).

        Args:
            agent_key: Key of the definition.
            question: The question to ask (4000 characters at most).
            expected: What a right answer says (4000 characters at most).

        Returns:
            The golden.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json(
            "POST",
            self._path(agent_key, "/goldens"),
            json={"question": question, "expected": expected},
        )

    async def goldens_remove(self, agent_key: str, golden_id: int) -> dict[str, Any]:
        """Remove a golden question.

        Args:
            agent_key: Key of the definition.
            golden_id: ID of the golden from :meth:`goldens_list`.

        Returns:
            Empty dict (the server answers 204).

        Raises:
            MammothValidationError: If *agent_key* is empty or *golden_id* is not positive.
        """
        self._check_id("golden_id", golden_id)
        return await self._client._request_json(
            "DELETE", self._path(agent_key, f"/goldens/{golden_id}")
        )

    async def goldens_run(self, agent_key: str) -> dict[str, Any]:
        """Start the proof run: the agent answers every golden under its current charter.

        Starting again while the same proof run is queued returns that run.

        Args:
            agent_key: Key of the definition.

        Returns:
            The proof run (202), see :meth:`goldens_status`.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("POST", self._path(agent_key, "/goldens/run"))

    async def goldens_status(self, agent_key: str) -> dict[str, Any]:
        """Get the latest proof run of a definition.

        Args:
            agent_key: Key of the definition.

        Returns:
            The proof run: status, passed and total.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("GET", self._path(agent_key, "/goldens/run"))

    async def notes_list(
        self,
        agent_key: str,
        project_id: int | None = None,
        kind: str | None = None,
    ) -> dict[str, Any]:
        """List a definition's notes: shared facts and working scratch notes.

        Args:
            agent_key: Key of the definition.
            project_id: Only notes of this project.
            kind: ``"fact"`` or ``"scratch"``.

        Returns:
            Dict with ``result``: the notes.

        Raises:
            MammothValidationError: If *agent_key* is empty or *kind* is not valid.
        """
        if kind is not None and kind not in VALID_NOTE_KINDS:
            raise MammothValidationError(ERR_NOTE_KIND.format(kind))
        params = _present(project_id=project_id, kind=kind)
        return await self._client._request_json(
            "GET", self._path(agent_key, "/notes"), params=params or None
        )

    async def notes_upsert(
        self, agent_key: str, project_id: int, kind: str, name: str, content: str
    ) -> dict[str, Any]:
        """Save a note, replacing the one with the same project, kind and name.

        Args:
            agent_key: Key of the definition.
            project_id: Project the note belongs to (one the agent is assigned to).
            kind: ``"fact"`` (learned, shared) or ``"scratch"`` (working notes).
            name: Note name (120 characters at most).
            content: Note text (8000 characters at most).

        Returns:
            The note.

        Raises:
            MammothValidationError: If *agent_key* is empty, *project_id* is not
                positive or *kind* is not valid.
        """
        self._check_id("project_id", project_id)
        if kind not in VALID_NOTE_KINDS:
            raise MammothValidationError(ERR_NOTE_KIND.format(kind))
        return await self._client._request_json(
            "PUT",
            self._path(agent_key, "/notes"),
            json={"project_id": project_id, "kind": kind, "name": name, "content": content},
        )

    async def notes_delete(self, agent_key: str, note_id: int) -> dict[str, Any]:
        """Delete one note.

        Args:
            agent_key: Key of the definition.
            note_id: ID of the note from :meth:`notes_list`.

        Returns:
            Empty dict (the server answers 204).

        Raises:
            MammothValidationError: If *agent_key* is empty or *note_id* is not positive.
        """
        self._check_id("note_id", note_id)
        return await self._client._request_json(
            "DELETE", self._path(agent_key, f"/notes/{note_id}")
        )

    async def feedback_list(self, agent_key: str) -> dict[str, Any]:
        """List the thumbs up/down feedback people gave this agent's answers.

        Args:
            agent_key: Key of the definition.

        Returns:
            Dict with ``result``: ``{session_id, turn_id, sign, text, by, at, question, answer}``.

        Raises:
            MammothValidationError: If *agent_key* is empty.
        """
        return await self._client._request_json("GET", self._path(agent_key, "/feedback"))


def _present(**fields: Any) -> dict[str, Any]:
    """Return the fields that are not None."""
    return {name: value for name, value in fields.items() if value is not None}
