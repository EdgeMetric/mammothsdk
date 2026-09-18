"""AI/LLM features API client for Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

# ── Validation error constants ────────────────────────────────────────────────

ERR_GENAI_PROMPT_EMPTY = "`prompt` must be a non-empty string."
ERR_GENAI_ROWS_RANGE = "`no_of_rows` must be between 1 and 100 (inclusive), got {0}."
ERR_EXPRESSION_MODE_INVALID = "`mode` must be 'math' or 'metric', got {0!r}."
ERR_RETENTION_MODE_INVALID = "`mode` must be 'generate' or 'test', got {0!r}."
ERR_RETENTION_INTENT_REQUIRED = "`intent` must be a non-empty string when `mode` is 'generate'."
ERR_RETENTION_CONDITION_REQUIRED = (
    "`condition_sql` must be a non-empty string when `mode` is 'test'."
)


class AIAPI:
    """Client for AI-powered features: profiling, generation, suggestions, SQL generation.

    Access via client.ai:
        client.ai.generate_profile(dataview_id=1039)
        client.ai.generate_sql(intent="total sales by region")
        suggestions = client.ai.get_suggestions()
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self) -> int:
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")
        return proj

    def _find_dataset(self, dataview_id: int, dataset_id: int | None = None) -> int:
        """Find dataset for a dataview."""
        if dataset_id is not None:
            return dataset_id
        return self._client.pipeline.find_dataset_for_dataview(dataview_id)

    PROFILE_ACTIONS: tuple[str, ...] = ("stats", "insights", "data_quality", "join_recommendation")

    def generate_profile(
        self,
        dataview_id: int,
        dataset_id: int | None = None,
        action: str = "insights",
    ) -> dict[str, Any]:
        """Generate an AI profile/summary of the dataview data.

        Corresponds to the backend ``ProfileGenerationSpec``:
        ``{"params": {"action": <action>}}``.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: ID of the dataset (auto-detected if not provided).
            action: One of ``"stats"``, ``"insights"`` (default),
                ``"data_quality"`` or ``"join_recommendation"``.

        Returns:
            Dict with profile information.

        Raises:
            MammothValidationError: If ``action`` is not a supported value.
        """
        if action not in self.PROFILE_ACTIONS:
            raise MammothValidationError(
                f"action must be one of {list(self.PROFILE_ACTIONS)}, got {action!r}.",
                {"action": action},
            )
        ws = self._ws()
        proj = self._proj()
        ds = self._find_dataset(dataview_id, dataset_id)
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{ds}/dataviews/{dataview_id}/profile_generation",
            json={"params": {"action": action}},
        )
        return self._client._wait_if_job(response)

    def generate_data(
        self,
        dataview_id: int,
        prompt: str,
        no_of_rows: int = 10,
        columns: list[str] | None = None,
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate synthetic data for a dataview.

        Corresponds to the backend ``GenAISpec``:
        ``{prompt, no_of_rows (1–100), columns}``.

        Args:
            dataview_id: ID of the dataview.
            prompt: Non-empty string describing what data to generate.
            no_of_rows: Number of rows to generate (1–100, default 10).
            columns: Optional list of column names to fill.
            dataset_id: ID of the dataset (auto-detected if not provided).

        Returns:
            Dict with generation result or job info.

        Raises:
            MammothValidationError: If ``prompt`` is empty or ``no_of_rows``
                is outside the 1–100 range.
        """
        if not prompt or not prompt.strip():
            raise MammothValidationError(ERR_GENAI_PROMPT_EMPTY)
        if not (1 <= no_of_rows <= 100):
            raise MammothValidationError(ERR_GENAI_ROWS_RANGE.format(no_of_rows))
        ws = self._ws()
        proj = self._proj()
        ds = self._find_dataset(dataview_id, dataset_id)
        body: dict[str, Any] = {"prompt": prompt, "no_of_rows": no_of_rows}
        if columns is not None:
            body["columns"] = columns
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{ds}/dataviews/{dataview_id}/data/generate",
            json=body,
        )
        return self._client._wait_if_job(response)

    def get_data_gen_info(
        self,
        dataview_id: int,
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """Get data generation information for a dataview.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: ID of the dataset (auto-detected if not provided).

        Returns:
            Dict with data generation info.
        """
        ws = self._ws()
        proj = self._proj()
        ds = self._find_dataset(dataview_id, dataset_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{ds}/dataviews/{dataview_id}/data/generate",
        )

    def generate_sql(
        self,
        intent: str,
        sequence_number: int = 0,
        dataset_id: int | None = None,
        dataview_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate SQL from natural language intent.

        Uses the project-level sql_generation endpoint, which requires the
        ``dataset_id`` query parameter (``dataview_id`` optional).

        Args:
            intent: Natural language description of the query.
            sequence_number: Sequence number for the SQL generation request.
            dataset_id: Dataset the SQL is generated against (required).
            dataview_id: Optional dataview within that dataset.

        Returns:
            Dict with generated SQL and metadata.
        """
        if dataset_id is None:
            raise MammothValidationError("generate_sql requires `dataset_id`.")
        ws = self._ws()
        proj = self._proj()
        params: dict[str, Any] = {"dataset_id": dataset_id}
        if dataview_id is not None:
            params["dataview_id"] = dataview_id
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/sql_generation",
            params=params,
            json={"params": {"intent": intent, "sequence_number": sequence_number}},
        )
        return self._client._wait_if_job(response)

    SUGGESTION_TYPES: tuple[str, ...] = (
        "extract_text",
        "add_condition",
        "generate_task",
        "apply_ai_template",
        "dashboards",
        "derivative_fuzzy_bucket",
    )

    def get_suggestions(
        self,
        suggestion_type: str | None = None,
        params: dict[str, Any] | None = None,
        dataset_id: int | None = None,
        dataview_id: int | None = None,
    ) -> dict[str, Any]:
        """Get AI-powered suggestions for the current project.

        Corresponds to the backend ``UnifiedPromptSpec``:
        ``{"suggestion_type": <type>, "params": {...}}`` where the ``params``
        shape depends on the type (e.g. ``generate_task`` takes ``{"prompt"}``,
        ``add_condition`` takes ``{"prompt", "sequence_number"}``,
        ``extract_text`` takes ``{"column_name", "sequence_number", "prompt"}``).

        Args:
            suggestion_type: One of ``extract_text``, ``add_condition``,
                ``generate_task``, ``apply_ai_template``, ``dashboards`` or
                ``derivative_fuzzy_bucket`` (required).
            params: Type-specific parameters (required).
            dataset_id: Optional dataset to scope the suggestions to
                (query parameter).
            dataview_id: Optional dataview to scope the suggestions to
                (query parameter).

        Returns:
            Dict with suggestions.

        Raises:
            MammothValidationError: If ``suggestion_type`` or ``params`` is
                missing or the type is unknown.
        """
        if suggestion_type not in self.SUGGESTION_TYPES:
            raise MammothValidationError(
                f"suggestion_type must be one of {list(self.SUGGESTION_TYPES)}, "
                f"got {suggestion_type!r}.",
                {"suggestion_type": suggestion_type},
            )
        if params is None:
            raise MammothValidationError(
                "get_suggestions requires `params` matching the suggestion_type.",
                {"suggestion_type": suggestion_type},
            )
        ws = self._ws()
        proj = self._proj()
        query: dict[str, Any] = {}
        if dataset_id is not None:
            query["dataset_id"] = dataset_id
        if dataview_id is not None:
            query["dataview_id"] = dataview_id
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/suggestions",
            params=query or None,
            json={"suggestion_type": suggestion_type, "params": params},
        )
        return self._client._wait_if_job(response)

    def query_gen(
        self,
        connector_key: str,
        connection_key: str,
        query: str,
        project_id: int | None = None,
        profile: str | None = None,
    ) -> dict[str, Any]:
        """Generate a query for a connector using AI.

        Corresponds to the backend ``Intent`` body: ``{"query": <intent>,
        "profile": <optional profile>}``.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            query: Natural language intent describing the query.
            project_id: Project ID (uses client default if not provided).
            profile: Optional connector profile name.

        Returns:
            Dict with generated query.
        """
        ws = self._ws()
        proj = project_id if project_id is not None else self._proj()
        body: dict[str, Any] = {"query": query}
        if profile is not None:
            body["profile"] = profile
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/chat",
            json=body,
        )
        return self._client._wait_if_job(response)

    def status(
        self,
        connector_key: str,
        connection_key: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get the status of an AI chat session for a connector connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with chat status information.
        """
        ws = self._ws()
        proj = project_id if project_id is not None else self._proj()
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}"
            f"/connections/{connection_key}/chat",
        )

    def condition_generate(
        self,
        intent: str,
        dataset_id: int,
        dataview_id: int | None = None,
        sequence_number: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate a filter condition from a natural language intent.

        Corresponds to the backend ``ConditionGenerationSpec``:
        ``{params: {intent, sequence_number}}``.

        Args:
            intent: Natural language description of the desired condition.
            dataset_id: ID of the dataset to generate the condition against.
            dataview_id: Optional ID of the dataview for column context.
            sequence_number: Optional sequence order in the pipeline.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the generated condition.
        """
        ws = self._ws()
        proj = project_id if project_id is not None else self._proj()
        params: dict[str, Any] = {"dataset_id": dataset_id}
        if dataview_id is not None:
            params["dataview_id"] = dataview_id
        body_params: dict[str, Any] = {"intent": intent}
        if sequence_number is not None:
            body_params["sequence_number"] = sequence_number
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/sql_generation/condition",
            params=params,
            json={"params": body_params},
        )
        return self._client._wait_if_job(response)

    def expression_generate(
        self,
        intent: str,
        mode: str,
        dataset_id: int,
        dataview_id: int | None = None,
        sequence_number: int | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate a math/metric expression from a natural language intent.

        Corresponds to the backend ``ExpressionGenerationSpec``:
        ``{params: {intent, mode, sequence_number}}``.

        Args:
            intent: Natural language description of the desired expression.
            mode: ``"math"`` for a row-level numeric expression, or ``"metric"``
                for an aggregate 1-row-1-column expression.
            dataset_id: ID of the dataset to generate the expression against.
            dataview_id: Optional ID of the dataview for column context.
            sequence_number: Optional sequence order in the pipeline.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with the generated expression.

        Raises:
            MammothValidationError: If ``mode`` is not ``"math"`` or ``"metric"``.
        """
        if mode not in ("math", "metric"):
            raise MammothValidationError(ERR_EXPRESSION_MODE_INVALID.format(mode))
        ws = self._ws()
        proj = project_id if project_id is not None else self._proj()
        params: dict[str, Any] = {"dataset_id": dataset_id}
        if dataview_id is not None:
            params["dataview_id"] = dataview_id
        body_params: dict[str, Any] = {"intent": intent, "mode": mode}
        if sequence_number is not None:
            body_params["sequence_number"] = sequence_number
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/sql_generation/expression",
            params=params,
            json={"params": body_params},
        )
        return self._client._wait_if_job(response)

    def retention_condition(
        self,
        dataset_id: int,
        mode: str,
        intent: str | None = None,
        condition_sql: str | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate or test a retention-policy WHERE clause.

        ``mode='generate'`` requires a natural-language ``intent`` and may
        return an asynchronous job. ``mode='test'`` requires ``condition_sql``
        and returns per-batch row counts (the API's union response may still
        be a job envelope). The request is always explicitly scoped to the
        client's workspace and selected project.
        """
        if isinstance(dataset_id, bool) or not isinstance(dataset_id, int) or dataset_id < 0:
            raise MammothValidationError("`dataset_id` must be an integer >= 0.")
        if mode not in ("generate", "test"):
            raise MammothValidationError(ERR_RETENTION_MODE_INVALID.format(mode))
        if mode == "generate":
            if not isinstance(intent, str) or not intent.strip():
                raise MammothValidationError(ERR_RETENTION_INTENT_REQUIRED)
            if condition_sql is not None:
                raise MammothValidationError("`condition_sql` is only valid when `mode` is 'test'.")
        elif not isinstance(condition_sql, str) or not condition_sql.strip():
            raise MammothValidationError(ERR_RETENTION_CONDITION_REQUIRED)
        elif intent is not None:
            raise MammothValidationError("`intent` is only valid when `mode` is 'generate'.")

        ws = self._ws()
        if project_id is not None and (
            isinstance(project_id, bool) or not isinstance(project_id, int) or project_id < 1
        ):
            raise MammothValidationError("`project_id` must be an integer >= 1.")
        proj = project_id if project_id is not None else self._proj()
        response = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/sql_generation/retention_policy",
            params={"dataset_id": dataset_id},
            json={"mode": mode, "intent": intent, "condition_sql": condition_sql},
        )
        return self._client._wait_if_job(response)
