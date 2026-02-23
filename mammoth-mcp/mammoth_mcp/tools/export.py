"""Export tools — database, FTP/SFTP exports, export management."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    get_manager,
    handle_errors,
    log_tool_call,
    run_sync,
    success_response,
)
from mammoth_mcp.server import mcp


@mcp.tool()
@log_tool_call
@handle_errors
async def export_to_database(
    ctx: Context,
    view_id: int,
    db_type: str,
    # Common relational DB params (postgres, mysql, redshift)
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    table: str | None = None,
    username: str | None = None,
    password: str | None = None,
    # BigQuery params
    project_name: str | None = None,
    dataset_name: str | None = None,
    service_account_json: str | None = None,
    # Elasticsearch params
    index: str | None = None,
) -> dict[str, Any]:
    """Export view data to an external database.

    SECURITY NOTE: Database credentials (password, service_account_json) are passed through
    the LLM context and may appear in conversation logs. For production use, consider
    configuring exports directly in the Mammoth UI instead.

    Args:
        view_id: The dataview ID to export from.
        db_type: Database type — one of: postgres, mysql, bigquery, redshift, elasticsearch.
        host: Database host (postgres, mysql, redshift).
        port: Database port (postgres, mysql, redshift).
        database: Database name (postgres, mysql, redshift).
        table: Target table name (postgres, mysql, redshift).
        username: Database username (postgres, mysql, redshift). Sensitive — may appear in logs.
        password: Database password (postgres, mysql, redshift). Sensitive — may appear in logs.
        project_name: GCP project name (bigquery).
        dataset_name: BigQuery dataset name (bigquery).
        service_account_json: GCP service account JSON string (bigquery). Sensitive — may appear in logs.
        index: Elasticsearch index name (elasticsearch).
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    db = db_type.lower()

    if db == "postgres":
        if not all([host, port, database, table, username, password]):
            raise ValueError(
                "host, port, database, table, username, password are all required for postgres"
            )
        result = await run_sync(
            view.export.to_postgres,
            host=host,
            port=port,
            database=database,
            table=table,
            username=username,
            password=password,
        )

    elif db == "mysql":
        if not all([host, port, database, table, username, password]):
            raise ValueError(
                "host, port, database, table, username, password are all required for mysql"
            )
        result = await run_sync(
            view.export.to_mysql,
            host=host,
            port=port,
            database=database,
            table=table,
            username=username,
            password=password,
        )

    elif db == "bigquery":
        config: dict[str, Any] = {}
        if project_name:
            config["project_name"] = project_name
        if dataset_name:
            config["dataset_name"] = dataset_name
        if table:
            config["table"] = table
        if service_account_json:
            config["service_account_json"] = service_account_json
        result = await run_sync(view.export.to_bigquery, **config)

    elif db == "redshift":
        if not all([host, port, database, table, username, password]):
            raise ValueError(
                "host, port, database, table, username, password are all required for redshift"
            )
        result = await run_sync(
            view.export.to_redshift,
            host=host,
            port=port,
            database=database,
            table=table,
            username=username,
            password=password,
        )

    elif db == "elasticsearch":
        config = {}
        if host:
            config["host"] = host
        if port:
            config["port"] = port
        if index:
            config["index"] = index
        if username:
            config["username"] = username
        if password:
            config["password"] = password
        result = await run_sync(view.export.to_elasticsearch, **config)

    else:
        raise ValueError(
            f"Unknown db_type '{db_type}'. Use: postgres, mysql, bigquery, redshift, elasticsearch"
        )

    return success_response(result, f"Exported to {db_type}")


@mcp.tool()
@log_tool_call
@handle_errors
async def export_to_ftp(
    ctx: Context,
    view_id: int,
    host: str,
    path: str,
    username: str,
    password: str,
    port: int = 21,
) -> dict[str, Any]:
    """Export view data to an FTP server.

    SECURITY NOTE: Credentials are passed through the LLM context and may appear
    in conversation logs. For production use, configure exports in the Mammoth UI.

    Args:
        view_id: The dataview ID to export from.
        host: FTP server hostname.
        path: Remote file path on the FTP server.
        username: FTP username. Sensitive — may appear in logs.
        password: FTP password. Sensitive — may appear in logs.
        port: FTP port (default 21).
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(
        view.export.to_ftp,
        host=host,
        path=path,
        username=username,
        password=password,
        port=port,
    )
    return success_response(result, f"Exported to FTP {host}:{path}")


@mcp.tool()
@log_tool_call
@handle_errors
async def export_to_sftp(
    ctx: Context,
    view_id: int,
    host: str,
    path: str,
    username: str,
    password: str,
    port: int = 22,
) -> dict[str, Any]:
    """Export view data to an SFTP server.

    SECURITY NOTE: Credentials are passed through the LLM context and may appear
    in conversation logs. For production use, configure exports in the Mammoth UI.

    Args:
        view_id: The dataview ID to export from.
        host: SFTP server hostname.
        path: Remote file path on the SFTP server.
        username: SFTP username. Sensitive — may appear in logs.
        password: SFTP password. Sensitive — may appear in logs.
        port: SFTP port (default 22).
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(
        view.export.to_sftp,
        host=host,
        path=path,
        username=username,
        password=password,
        port=port,
    )
    return success_response(result, f"Exported to SFTP {host}:{path}")


@mcp.tool()
@log_tool_call
@handle_errors
async def list_exports(
    ctx: Context,
    view_id: int,
) -> dict[str, Any]:
    """List all exports configured on a view.

    Args:
        view_id: The dataview ID.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(view.export.list)
    return success_response(result, f"Found {len(result)} export(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_export(
    ctx: Context,
    view_id: int,
    export_id: int,
) -> dict[str, Any]:
    """Delete an export from a view's pipeline.

    Args:
        view_id: The dataview ID.
        export_id: The export ID to delete.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(view.export.delete, export_id)
    return success_response(result, f"Deleted export {export_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def publish_to_db(
    ctx: Context,
    view_id: int,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Publish view data to Mammoth's internal database for dashboard use.

    Args:
        view_id: The dataview ID to publish.
        config: Optional publish configuration.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    kwargs = config or {}
    result = await run_sync(view.export.publish_to_db, **kwargs)
    return success_response(result, f"Published view {view_id} to database")
