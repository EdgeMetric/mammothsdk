"""Connectors API client for managing cloud data source connectors and connections."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError
from mammoth.models.connectors import DsConfigPatchOp, DsConfigPatchPath

if TYPE_CHECKING:
    from ..client import MammothClient

_list = list  # Alias to avoid shadowing by method name

# ── Validation error constants ────────────────────────────────────────────────

ERR_CONNECTOR_KEY_EMPTY = "`connector_key` must be a non-empty string."
ERR_CONNECTION_CONFIG_EMPTY = (
    "`config` must be a non-empty dict containing connection credentials. "
    "Shape varies by connector_key. Examples: "
    "postgres/mysql/mssql → {hostname, port, database, username, password}; "
    "salesforce/hubspot/oauth connectors → {code}; "
    "snowflake → {url, username, password, database, warehouse, account, role}."
)
ERR_UPDATE_CONNECTION_CREDS_EMPTY = (
    "`credentials` must be a non-empty dict containing the updated connection "
    "credentials. Shape varies by connector_key (same as create_connection)."
)
ERR_DS_CONFIG_SOURCE_REQUIRED = (
    "Either `query` or `file_source` must be provided. "
    "Use `query` for database connectors (postgres, mysql, bigquery, etc.); "
    "use `file_source` for file connectors (SFTP, Google Drive, etc.)."
)
ERR_DS_CONFIG_VALIDATE_XOR = (
    "`validate` and `data_sample` are mutually exclusive; " "set at most one of them to True."
)
ERR_DS_CONFIG_PATCH_EMPTY = "`patch` must be a non-empty list of patch operations."
ERR_DS_CONFIG_PATCH_OP = "Each patch op must have op='replace', got {0!r}."
ERR_DS_CONFIG_PATCH_PATH = (
    "Each patch op path must be one of "
    "{query, profile, on_refresh_action, unique_sequence_column}, got {0!r}."
)


class ConnectorsAPI:
    """Client for managing cloud data source connectors and connections.

    Access via client.connectors:
        connectors = client.connectors.list()
        conn = client.connectors.create_connection("postgres", config={...})
        client.connectors.delete_connection("postgres", "conn_key")
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

    def list(self) -> _list[dict[str, Any]]:
        """List all available connectors.

        Returns:
            List of connector dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/connectors")
        if isinstance(response, _list):
            return response
        return response.get("connectors", [])

    def get(self, connector_key: str) -> dict[str, Any]:
        """Get details of a specific connector.

        Args:
            connector_key: Key identifying the connector type (e.g., "postgres", "mysql").

        Returns:
            Dict with connector details.
        """
        return self._client._request_json(
            "GET", f"/workspaces/{self._ws()}/connectors/{connector_key}"
        )

    def list_connections(
        self, connector_key: str, project_id: int | None = None
    ) -> _list[dict[str, Any]]:
        """List connections for a connector type.

        Args:
            connector_key: Key identifying the connector type.
            project_id: Project ID (uses client default if not provided).

        Returns:
            List of connection dicts.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        response = self._client._request(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections",
        )
        if isinstance(response, _list):
            return response
        return response.get("connections", [])

    def create_connection(
        self, connector_key: str, config: dict[str, Any], project_id: int | None = None
    ) -> dict[str, Any]:
        """Create a new connection for a connector.

        The ``config`` shape is per-connector and varies across the 25+ supported
        connector types. The SDK forwards it verbatim — the backend validates per
        connector_key. Common examples:

        - **DB connectors** (postgres, mysql, mssql, mongodb):
          ``{hostname, port, database, username, password}``
        - **Extended DB** (postgres, redshift):
          adds ``ssh_enabled``, ``proxy_*``, ``ssh_auth_type``, ``private_key``
        - **OAuth connectors** (salesforce, hubspot, facebook, …):
          ``{code}``
        - **Snowflake**: ``{url, username, password, database, warehouse, account, role}``
        - **BigQuery**: ``{connection_data}`` (JSON string)
        - **DataBricks**: ``{host, port, http_path, personal_access_token, catalog}``
        - **SFTP**: ``{username, domain, port, password | private_key}``

        Args:
            connector_key: Key identifying the connector type.
            config: Non-empty dict of connection credentials. Shape varies by
                connector_key — see above for common examples.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with created connection info.

        Raises:
            MammothValidationError: If ``config`` is empty.
        """
        if not config:
            raise MammothValidationError(ERR_CONNECTION_CONFIG_EMPTY)
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections",
            json=config,
        )

    def get_connection(
        self, connector_key: str, connection_key: str, project_id: int | None = None
    ) -> dict[str, Any]:
        """Get details of a specific connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with connection details.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}",
        )

    def update_connection(
        self,
        connector_key: str,
        connection_key: str,
        credentials: dict[str, Any],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a connection's credentials.

        The backend expects a JSON-patch envelope:
        ``{"patch": [{"op": "replace", "path": "connection", "value": <credentials>}]}``.
        This method accepts the raw credentials dict and wraps it internally.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            credentials: Non-empty dict of updated connection credentials. Shape
                is the same as for ``create_connection`` (varies by connector_key).
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with updated connection info.

        Raises:
            MammothValidationError: If ``credentials`` is empty.
        """
        if not credentials:
            raise MammothValidationError(ERR_UPDATE_CONNECTION_CREDS_EMPTY)
        ws = self._ws()
        proj = self._proj(project_id)
        body = {"patch": [{"op": "replace", "path": "connection", "value": credentials}]}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}",
            json=body,
        )

    def delete_connection(
        self, connector_key: str, connection_key: str, project_id: int | None = None
    ) -> dict[str, Any]:
        """Delete a connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}",
        )

    def list_ds_configs(
        self, connector_key: str, connection_key: str, project_id: int | None = None
    ) -> _list[dict[str, Any]]:
        """List data source configurations for a connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            project_id: Project ID (uses client default if not provided).

        Returns:
            List of data source config dicts.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        response = self._client._request(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs",
        )
        if isinstance(response, _list):
            return response
        return response.get("ds_configs", [])

    def create_ds_config(
        self,
        connector_key: str,
        connection_key: str,
        *,
        query: str | None = None,
        file_source: str | None = None,
        table: str | None = None,
        profile: str | None = None,
        validate: bool = True,
        data_sample: bool = False,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a data source configuration.

        Exactly one of ``query`` or ``file_source`` must be provided (mirrors the
        backend ``ValidateAndSampleDataSpec`` validator). ``validate`` and
        ``data_sample`` are mutually exclusive.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            query: SQL query or table reference (required for DB connectors).
            file_source: File path or source identifier (required for file connectors
                such as SFTP or Google Drive).
            table: Optional table name hint.
            profile: Optional connector-specific profile (e.g. schema name for DB
                connectors, or ``"project_id.dataset_id"`` for BigQuery).
            validate: If ``True`` (default), the backend validates the config.
                Mutually exclusive with ``data_sample``.
            data_sample: If ``True``, the backend returns a data sample.
                Mutually exclusive with ``validate``.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with created data source config.

        Raises:
            MammothValidationError: If neither ``query`` nor ``file_source`` is
                provided, or if both ``validate`` and ``data_sample`` are ``True``.
        """
        if not query and not file_source:
            raise MammothValidationError(ERR_DS_CONFIG_SOURCE_REQUIRED)
        if validate and data_sample:
            raise MammothValidationError(ERR_DS_CONFIG_VALIDATE_XOR)
        ws = self._ws()
        proj = self._proj(project_id)
        body: dict[str, Any] = {"validate": validate, "data_sample": data_sample}
        if query is not None:
            body["query"] = query
        if file_source is not None:
            body["file_source"] = file_source
        if table is not None:
            body["table"] = table
        if profile is not None:
            body["profile"] = profile
        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs",
            json=body,
        )

    def get_ds_config(
        self,
        connector_key: str,
        connection_key: str,
        ds_config_key: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Get a specific data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with data source config details.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "GET",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
        )

    def update_ds_config(
        self,
        connector_key: str,
        connection_key: str,
        ds_config_key: str,
        patch: _list[DsConfigPatchOp],
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Update a data source configuration via JSON-patch operations.

        The backend accepts a patch envelope:
        ``{"patch": [{"op": "replace", "path": "<path>", "value": <value>}]}``.

        Note: only ``path='query'`` is currently implemented on the backend;
        ``profile``, ``on_refresh_action``, and ``unique_sequence_column`` are
        accepted by the SDK but the server returns ``not_implemented_error``.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.
            patch: Non-empty list of :class:`~mammoth.models.connectors.DsConfigPatchOp`
                instances.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with updated config.

        Raises:
            MammothValidationError: If ``patch`` is empty, any op is not
                ``"replace"``, or any path is not a valid
                :class:`~mammoth.models.connectors.DsConfigPatchPath` value.
        """
        if not patch:
            raise MammothValidationError(ERR_DS_CONFIG_PATCH_EMPTY)
        for op in patch:
            if op.op != "replace":
                raise MammothValidationError(ERR_DS_CONFIG_PATCH_OP.format(op.op))
            valid_paths = {p.value for p in DsConfigPatchPath}
            path_val = op.path.value if isinstance(op.path, DsConfigPatchPath) else op.path
            if path_val not in valid_paths:
                raise MammothValidationError(ERR_DS_CONFIG_PATCH_PATH.format(path_val))
        ws = self._ws()
        proj = self._proj(project_id)
        body = {"patch": [{"op": p.op, "path": p.path.value, "value": p.value} for p in patch]}
        return self._client._request_json(
            "PATCH",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
            json=body,
        )

    def delete_ds_config(
        self,
        connector_key: str,
        connection_key: str,
        ds_config_key: str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete a data source configuration.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            ds_config_key: Key identifying the data source config.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}/connections/{connection_key}/ds_configs/{ds_config_key}",
        )

    def ds_config_delete_all(
        self,
        connector_key: str,
        connection_key: str,
        config_ids: _list[str] | str,
        project_id: int | None = None,
    ) -> dict[str, Any]:
        """Bulk-delete data source configurations for a connection.

        Args:
            connector_key: Key identifying the connector type.
            connection_key: Key identifying the connection.
            config_ids: List of data source config keys (or comma-separated
                string) to delete.
            project_id: Project ID (uses client default if not provided).

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        proj = self._proj(project_id)
        ids_str = ",".join(config_ids) if isinstance(config_ids, _list) else config_ids
        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/connectors/{connector_key}"
            f"/connections/{connection_key}/ds_configs",
            params={"config_ids": ids_str},
        )

    def active_connectors(self) -> _list[dict[str, Any]]:
        """List active connectors with established connections.

        Returns:
            List of active connector dicts.
        """
        response = self._client._request("GET", f"/workspaces/{self._ws()}/active_connectors")
        if isinstance(response, _list):
            return response
        return response.get("connectors", [])
