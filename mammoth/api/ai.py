"""
AI/LLM features API client for Mammoth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import MammothClient


class AIAPI:
    """Client for AI-powered features: profiling, generation, suggestions, SQL generation.

    Access via client.ai:
        client.ai.generate_profile(dataview_id=1039)
        client.ai.generate_sql(intent="total sales by region", dataview_ids=[1039])
        suggestions = client.ai.get_suggestions(dataview_id=1039)
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
        return self._client.pipeline._find_dataset_for_dataview(dataview_id)

    def generate_profile(
        self,
        dataview_id: int,
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate an AI profile/summary of the dataview data.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: ID of the dataset (auto-detected if not provided).

        Returns:
            Dict with profile information.
        """
        ws = self._ws()
        proj = self._proj()
        ds = self._find_dataset(dataview_id, dataset_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{ds}/dataviews/{dataview_id}/ai/profile",
        )

    def generate_data(
        self,
        dataview_id: int,
        config: dict[str, Any],
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate synthetic data for a dataview.

        Args:
            dataview_id: ID of the dataview.
            config: Generation configuration (rows, columns, patterns).
            dataset_id: ID of the dataset (auto-detected if not provided).

        Returns:
            Dict with generation result or job info.
        """
        ws = self._ws()
        proj = self._proj()
        ds = self._find_dataset(dataview_id, dataset_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{ds}/dataviews/{dataview_id}/ai/generate",
            json=config,
        )

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
            f"/workspaces/{ws}/projects/{proj}/datasets/{ds}/dataviews/{dataview_id}/ai/generate",
        )

    def generate_sql(
        self,
        intent: str,
        dataview_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Generate SQL from natural language intent.

        Args:
            intent: Natural language description of the query.
            dataview_ids: List of dataview IDs to use as context (optional).

        Returns:
            Dict with generated SQL and metadata.
        """
        ws = self._ws()
        payload: dict[str, Any] = {"intent": intent}
        if dataview_ids:
            payload["dataview_ids"] = dataview_ids
        return self._client._request_json("POST", f"/workspaces/{ws}/ai/sql", json=payload)

    def get_suggestions(
        self,
        dataview_id: int,
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        """Get AI-powered transformation suggestions for a dataview.

        Args:
            dataview_id: ID of the dataview.
            dataset_id: ID of the dataset (auto-detected if not provided).

        Returns:
            Dict with suggested transformations.
        """
        ws = self._ws()
        proj = self._proj()
        ds = self._find_dataset(dataview_id, dataset_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{ds}/dataviews/{dataview_id}/ai/suggestions",
        )

    def query_gen(
        self,
        connector_key: str,
        connection_key: str,
        prompt: str,
    ) -> dict[str, Any]:
        """Generate a query for a connector using AI.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            prompt: Natural language prompt describing the query.

        Returns:
            Dict with generated query.
        """
        ws = self._ws()
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/connectors/{connector_key}/connections/{connection_key}/query_gen",
            json={"prompt": prompt},
        )
