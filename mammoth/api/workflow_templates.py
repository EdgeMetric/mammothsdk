"""Workflow template catalog API client: list, rank, fit, preview and build workflow templates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from mammoth.client import MammothClient

_list = list  # Alias to avoid shadowing by the `list` method name

ERR_PROJECT_ID_POSITIVE = "`project_id` must be a positive integer, got {0}."
ERR_KEY_EMPTY = "`key` must be a non-empty template key (see `workflow_templates.list`)."
ERR_INPUT_EMPTY = "`input_key` must be a non-empty input key of the template."
ERR_DATASET_IDS = "`dataset_ids` must be 1 to 200 positive dataset ids, got {0!r}."
ERR_INPUTS = "`inputs` must map each input key to a positive dataset id, got {0!r}."
ERR_DESTINATION = "`destination_name` must be 1 to 120 characters."
_DATASET_IDS_MAX = 200
_DESTINATION_MAX = 120


class WorkflowTemplatesAPI:
    """Client for the project workflow-template catalog.

    The catalog is the set of ready-made workflows (``GET .../workflow-templates``);
    it is not the workspace templates of ``client.templates`` (the legacy
    ``/workspaces/{ws}/templates`` API) nor ``client.workflows.from_template``, which
    copies one of those. A template names its inputs (tables) and the roles its steps
    read in them (the columns). Use it in order: ``list`` or ``get`` to pick one,
    ``rank`` to find the project tables that fit an input, ``fit`` to match columns to
    roles, ``preview`` to run it on your rows and ``build`` to add it to a workflow.

    Access via ``client.workflow_templates``::

        cards = await client.workflow_templates.list()
        detail = await client.workflow_templates.get(cards[0]["key"])
        fit = await client.workflow_templates.fit(detail["key"], {"main": 4521})
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _base(self, project_id: int | None) -> str:
        if project_id is not None and project_id <= 0:
            raise MammothValidationError(ERR_PROJECT_ID_POSITIVE.format(project_id))
        proj = project_id if project_id is not None else getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        return f"/workspaces/{self._client.workspace_id}/projects/{proj}/workflow-templates"

    def _template_path(self, key: str, project_id: int | None, tail: str = "") -> str:
        if not isinstance(key, str) or not key.strip():
            raise MammothValidationError(ERR_KEY_EMPTY)
        return f"{self._base(project_id)}/{quote(key.strip(), safe='')}{tail}"

    @staticmethod
    def _check_inputs(inputs: dict[str, int]) -> None:
        if not isinstance(inputs, dict) or not inputs:
            raise MammothValidationError(ERR_INPUTS.format(inputs))
        for name, dataset_id in inputs.items():
            bad = not isinstance(dataset_id, int) or isinstance(dataset_id, bool)
            if not isinstance(name, str) or not name or bad or dataset_id <= 0:
                raise MammothValidationError(ERR_INPUTS.format(inputs))

    @staticmethod
    def _use_body(
        inputs: dict[str, int],
        matches: dict[str, dict[str, dict[str, Any]]],
        settings: dict[str, Any] | None,
    ) -> dict[str, Any]:
        WorkflowTemplatesAPI._check_inputs(inputs)
        body: dict[str, Any] = {"inputs": inputs, "matches": matches}
        if settings is not None:
            body["settings"] = settings
        return body

    async def list(self, project_id: int | None = None) -> dict[str, Any]:
        """List the catalog's workflow templates, most searched first within each family.

        Args:
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"templates": [...]}``, one card per template: ``key``, ``name``, ``family``,
            ``sentence``, ``needs``, ``gives``, ``inputs`` (``key``, ``label``), ``output`` and
            ``words`` (what people search it by). The backend answers with a bare JSON array,
            which is wrapped so callers get the usual dict shape.

        Raises:
            MammothValidationError: If *project_id* is not a positive integer.
        """
        cards = await self._client._request_list("GET", self._base(project_id))
        return {"templates": cards}

    async def get(self, key: str, project_id: int | None = None) -> dict[str, Any]:
        """Get a template's inputs, roles and settings.

        Args:
            key: The template's key, from ``list``.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The card plus ``result_name``, ``main`` (the main input's key), ``inputs`` with
            each input's ``roles`` and ``settings``.

        Raises:
            MammothValidationError: If *key* is empty or *project_id* is not positive.
        """
        return await self._client._request_json("GET", self._template_path(key, project_id))

    async def sample_result(self, key: str, project_id: int | None = None) -> dict[str, Any]:
        """Show a template's result on its own sample rows (computed in memory, nothing imported).

        Args:
            key: The template's key.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The result's columns and rows with ``input_rows`` and ``steps``.

        Raises:
            MammothValidationError: If *key* is empty or *project_id* is not positive.
        """
        return await self._client._request_json(
            "GET", self._template_path(key, project_id, "/sample-result")
        )

    async def rank(
        self,
        key: str,
        input_key: str,
        dataset_ids: _list[int],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Rank project tables by how well they fit one input of a template (columns only).

        Args:
            key: The template's key.
            input_key: The input's key, from the template's ``inputs``.
            dataset_ids: The tables to rank (1 to 200 dataset ids).
            project_id: Project ID (uses the client default if not provided).

        Returns:
            ``{"tables": [...]}``, one ``{dataset_id, found, roles, missing}`` per table that
            could be read: roles found, roles in the input and the required roles missing.
            The backend answers with a bare JSON array, which is wrapped.

        Raises:
            MammothValidationError: If an argument is empty, not positive or too long.
        """
        if not isinstance(input_key, str) or not input_key.strip():
            raise MammothValidationError(ERR_INPUT_EMPTY)
        bad = not isinstance(dataset_ids, list) or not 1 <= len(dataset_ids) <= _DATASET_IDS_MAX
        if bad or any(not isinstance(i, int) or isinstance(i, bool) or i <= 0 for i in dataset_ids):
            raise MammothValidationError(ERR_DATASET_IDS.format(dataset_ids))
        ranked = await self._client._request_list(
            "POST",
            self._template_path(key, project_id, "/rank"),
            json={"input": input_key.strip(), "dataset_ids": dataset_ids},
        )
        return {"tables": ranked}

    async def fit(
        self, key: str, inputs: dict[str, int], project_id: int | None = None
    ) -> dict[str, Any]:
        """Match a template's roles to the columns of the tables you chose.

        Args:
            key: The template's key.
            inputs: Input key -> dataset id.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            Each table's columns and the column proposed for every role.

        Raises:
            MammothValidationError: If *key* is empty or *inputs* is not input key -> dataset id.
        """
        self._check_inputs(inputs)
        return await self._client._request_json(
            "POST", self._template_path(key, project_id, "/fit"), json={"inputs": inputs}
        )

    async def preview(
        self,
        key: str,
        inputs: dict[str, int],
        matches: dict[str, dict[str, dict[str, Any]]],
        settings: dict[str, Any] | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Run a template on the first rows of your tables and run its checks.

        Args:
            key: The template's key.
            inputs: Input key -> dataset id.
            matches: Input key -> role key -> the column(s) playing it, for example
                ``{"main": {"amount": {"column": "Amount"}}}``. A role takes ``column``,
                ``columns``, or ``debit`` and ``credit`` with ``sign``, and ``negate``.
            settings: Setting key -> value; the template's defaults when omitted.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            The template's result on your rows and its checks.

        Raises:
            MammothValidationError: If *key* is empty or *inputs* is not input key -> dataset id.
        """
        return await self._client._request_json(
            "POST",
            self._template_path(key, project_id, "/preview"),
            json=self._use_body(inputs, matches, settings),
        )

    async def import_samples(self, key: str, project_id: int | None = None) -> dict[str, Any]:
        """Import a template's sample tables into the project (once), to try it without data.

        Args:
            key: The template's key.
            project_id: Project ID (uses the client default if not provided).

        Returns:
            Dict with ``inputs``: input key -> the dataset id of its sample table.

        Raises:
            MammothValidationError: If *key* is empty or *project_id* is not positive.
        """
        return await self._client._request_json(
            "POST", self._template_path(key, project_id, "/samples")
        )

    async def build(
        self,
        key: str,
        inputs: dict[str, int],
        matches: dict[str, dict[str, dict[str, Any]]],
        destination_name: str,
        settings: dict[str, Any] | None = None,
        destination_emails: _list[str] | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Add a template's steps to a workflow and start the Save that builds them.

        The server refuses a build whose own preview could not run. It answers 202 while the
        Save runs; follow it with ``client.workflows.get(workflow_id)``.

        Args:
            key: The template's key.
            inputs: Input key -> dataset id.
            matches: Input key -> role key -> the column(s) playing it (see ``preview``).
            destination_name: The result table's name (1 to 120 characters).
            settings: Setting key -> value; the template's defaults when omitted.
            destination_emails: People to email the result to (at most 20).
            project_id: Project ID (uses the client default if not provided).

        Returns:
            Dict with the ``workflow`` whose ``canvas_state.save_run`` is the Save in progress.

        Raises:
            MammothValidationError: If *key*, *inputs* or *destination_name* is invalid.
        """
        name = destination_name.strip() if isinstance(destination_name, str) else ""
        if not 1 <= len(name) <= _DESTINATION_MAX:
            raise MammothValidationError(ERR_DESTINATION)
        body = self._use_body(inputs, matches, settings)
        body["destination"] = {"name": name, "emails": destination_emails or []}
        return await self._client._request_json(
            "POST", self._template_path(key, project_id, "/build"), json=body
        )
