"""Batches API client for managing dataset batches in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError
from mammoth.models.batches import BatchesPostRequest

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
        mapping: dict[str, str] | _list[dict[str, Any]],
        project_id: int | None = None,
        new_ds_params: dict[str, Any] | None = None,
        is_validation_required: bool | None = None,
        change_map: dict[str, Any] | None = None,
        delete_source_ds: bool = False,
        expected_destination_c_type: str = "TEXT",
    ) -> dict[str, Any]:
        """Create a new batch for a dataset.


        Args:
            dataset_id: ID of the destination dataset.
            source_id: ID of the source dataset (must be a positive integer).
            mapping: Non-empty ``{"src_col": "dst_col"}`` dict (expanded to
                ``ColumnNameMapping`` items, each stamped with
                ``expected_destination_c_type``) or an explicit list of
                ``ColumnNameMapping`` / ``ColumnIdMapping`` objects, every
                item carrying its own ``expected_destination_c_type``
                (``TEXT``, ``NUMERIC`` or ``DATE``; the route requires it).
            project_id: Project ID (uses client default if not provided).
            new_ds_params: Optional params for creating a new dataset.
            is_validation_required: Whether to validate the batch.
            change_map: Optional change-tracking column map.
            delete_source_ds: Whether to delete the source dataset after batch
                (default ``False``).
            expected_destination_c_type: Type stamped on every item of a
                ``{src: dst}`` mapping dict (default ``"TEXT"``); ignored for
                list mappings, which carry their own.

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
        # ``BatchesPostRequest``: ``mapping`` is a list of ``ColumnNameMapping``
        # (``source_c_name``/``destination_c_name``) or ``ColumnIdMapping``
        # items; the ``{src: dst}`` dict shortcut is expanded to the former.
        if expected_destination_c_type not in ("TEXT", "NUMERIC", "DATE"):
            raise MammothValidationError(
                "expected_destination_c_type must be TEXT, NUMERIC or DATE, "
                f"got {expected_destination_c_type!r}.",
                {"expected_destination_c_type": expected_destination_c_type},
            )
        mapping_items: list[dict[str, Any]] = (
            [
                {
                    "source_c_name": source,
                    "destination_c_name": destination,
                    "expected_destination_c_type": expected_destination_c_type,
                }
                for source, destination in mapping.items()
            ]
            if isinstance(mapping, dict)
            else list(mapping)
        )
        for item in mapping_items:
            if "expected_destination_c_type" not in item:
                raise MammothValidationError(
                    "Every mapping item needs `expected_destination_c_type` "
                    "(TEXT, NUMERIC or DATE); the batches route rejects items without it.",
                    {"mapping_item": item},
                )
        body: dict[str, Any] = {
            "source_id": source_id,
            "mapping": mapping_items,
            "delete_source_ds": delete_source_ds,
        }
        if new_ds_params is not None:
            body["new_ds_details"] = new_ds_params
        if is_validation_required is not None:
            body["validate_only"] = is_validation_required
        if change_map is not None:
            body["change_map"] = change_map
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            json=body,
        )

    def create_spec(
        self,
        dataset_id: int,
        spec: BatchesPostRequest | dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a batch using the release ``BatchesPostRequest`` shape.

        This additive method preserves the older ``create`` contract while
        supporting either ``source_id`` plus array ``mapping`` or ``file_id``
        alone.  The CLI owns confirmation policy for destructive calls.
        """
        if isinstance(dataset_id, bool) or not isinstance(dataset_id, int) or dataset_id <= 0:
            raise MammothValidationError(
                f"`dataset_id` must be a positive integer, got {dataset_id}."
            )
        if project_id is not None and (
            isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0
        ):
            raise MammothValidationError(
                f"`project_id` must be a positive integer, got {project_id}."
            )
        if isinstance(self._ws(), bool) or not isinstance(self._ws(), int) or self._ws() <= 0:
            raise MammothValidationError(
                f"`workspace_id` must be a positive integer, got {self._ws()}."
            )
        try:
            typed = BatchesPostRequest.model_validate(spec)
        except Exception as exc:
            raise MammothValidationError(f"Invalid release batch spec: {exc}") from exc
        source_id = typed.source_id
        file_id = typed.file_id
        if source_id is None and file_id is None:
            raise MammothValidationError("Either `source_id` or `file_id` is required.")
        if source_id is not None and file_id is not None:
            raise MammothValidationError("`source_id` and `file_id` are mutually exclusive.")
        if source_id is not None and source_id <= 0:
            raise MammothValidationError(ERR_BATCH_SOURCE_ID_POSITIVE.format(source_id))
        if file_id is not None and file_id <= 0:
            raise MammothValidationError(f"`file_id` must be a positive integer, got {file_id}.")
        mapping = typed.mapping
        if source_id is not None and not mapping:
            raise MammothValidationError("`mapping` must be a non-empty release mapping array.")
        if file_id is not None and mapping is not None:
            raise MammothValidationError("`mapping` must be omitted when `file_id` is provided.")
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            json=typed.model_dump(mode="json", exclude_unset=True),
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

    def bulk_delete(
        self,
        dataset_id: int,
        ids: _list[int] | str | None = None,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Bulk-delete batches for a dataset.

        Args:
            dataset_id: ID of the dataset.
            ids: Optional list of batch IDs (or comma-separated string) to
                delete. If omitted, all batches for the dataset are deleted.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        params: dict[str, Any] = {}
        if ids is not None:
            params["ids"] = ",".join(str(i) for i in ids) if isinstance(ids, _list) else ids
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{dataset_id}/batches",
            params=params or None,
        )
