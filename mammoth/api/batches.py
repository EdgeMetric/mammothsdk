"""Batches API client for managing dataset batches in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

# ── Validation error constants ────────────────────────────────────────────────

ERR_BATCH_SOURCE_ID_POSITIVE = "`source_id` must be a positive integer, got {0}."
ERR_BATCH_MAPPING_EMPTY = (
    "`mapping` must be a non-empty dict mapping source columns to destination columns."
)
ERR_BATCH_PATCH_EMPTY = "`patch` must be a non-empty list of patch operations."
ERR_BATCH_PATCH_OP = "Each patch op must have op='replace' or op='remove', got {0!r}."


class BatchesAPI:
    """Client for managing dataset batch operations.

    Access via client.batches::

        batches = client.batches.list(dataset_id=123)
        batch = client.batches.get(dataset_id=123, batch_id=1)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def _proj(self, project_id: int | None = None) -> int:
        if project_id is not None:
            return project_id
        proj = getattr(self._client, "project_id", None)
        if proj is not None:
            return proj
        raise ValueError("project_id must be set on the client using client.set_project_id()")

    def list(
        self,
        dataset_id: int,
        project_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List batches for a dataset.

        Args:
            dataset_id: ID of the dataset.
            project_id: Project ID (uses client default if not provided).
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).

        Returns:
            Dict with batches list and pagination info.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {}
        if limit != 50:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            params=params or None,
        )

    def get(
        self,
        dataset_id: int,
        batch_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get batch details.

        Args:
            dataset_id: ID of the dataset.
            batch_id: ID of the batch.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with batch details.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches/{batch_id}",
        )

    def create(
        self,
        dataset_id: int,
        source_id: int,
        mapping: dict[str, str],
        project_id: int | None = None,
        new_ds_params: dict[str, Any] | None = None,
        is_validation_required: bool | None = None,
        change_map: dict[str, Any] | None = None,
        delete_source_ds: bool = False,
    ) -> dict[str, Any]:
        """Create a new batch for a dataset.

        The ``source`` field is hardcoded to ``"datasource"`` — the only
        supported source type.

        Args:
            dataset_id: ID of the destination dataset.
            source_id: ID of the source dataset (must be a positive integer).
            mapping: Non-empty dict mapping source column names to destination
                column names, e.g. ``{"src_col": "dst_col"}``.
            project_id: Project ID (uses client default if not provided).
            new_ds_params: Optional params for creating a new dataset.
            is_validation_required: Whether to validate the batch.
            change_map: Optional change-tracking column map.
            delete_source_ds: Whether to delete the source dataset after batch
                (default ``False``).

        Returns:
            Dict with created batch info.

        Raises:
            MammothValidationError: If ``source_id`` is not positive or ``mapping``
                is empty.
        """
        if source_id <= 0:
            raise MammothValidationError(ERR_BATCH_SOURCE_ID_POSITIVE.format(source_id))
        if not mapping:
            raise MammothValidationError(ERR_BATCH_MAPPING_EMPTY)
        ws = self._ws()
        proj = self._proj(project_id)
        body: dict[str, Any] = {
            "source": "datasource",
            "source_id": source_id,
            "mapping": mapping,
            "delete_source_ds": delete_source_ds,
        }
        if new_ds_params is not None:
            body["new_ds_params"] = new_ds_params
        if is_validation_required is not None:
            body["is_validation_required"] = is_validation_required
        if change_map is not None:
            body["change_map"] = change_map
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            json=body,
        )

    def update(
        self,
        dataset_id: int,
        patch: _list[dict[str, Any]],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update batches for a dataset via patch operations.

        The backend expects ``{"patch": [<ops>]}``. Each op has:

        - ``op``: ``"replace"`` or ``"remove"``
        - ``value``: for ``replace`` — a dict mapping operation name to list of
          batch IDs; for ``remove`` — a list of batch IDs.

        Args:
            dataset_id: ID of the dataset.
            patch: Non-empty list of patch operation dicts.  Each dict must
                include ``"op"`` (``"replace"`` or ``"remove"``) and ``"value"``.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with updated batch info.

        Raises:
            MammothValidationError: If ``patch`` is empty or any op has an
                invalid ``op`` value.
        """
        if not patch:
            raise MammothValidationError(ERR_BATCH_PATCH_EMPTY)
        valid_ops: set[str] = {"replace", "remove"}
        for op in patch:
            if op.get("op") not in valid_ops:
                raise MammothValidationError(ERR_BATCH_PATCH_OP.format(op.get("op")))
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            json={"patch": patch},
        )

    def delete(
        self,
        dataset_id: int,
        batch_id: int,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a batch.

        Args:
            dataset_id: ID of the dataset.
            batch_id: ID of the batch.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches/{batch_id}",
        )
