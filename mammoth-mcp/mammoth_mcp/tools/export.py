"""Export tools — CSV, S3, email, database exports."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    error_response,
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
async def export_data(
    ctx: Context,
    view_id: int,
    format: str,
    dataset_id: int | None = None,
    # S3 options
    file_name: str | None = None,
    file_type: str = "csv",
    # email options
    recipients: list[str] | None = None,
    # dataset (branch out) options
    dest_dataset_id: int | None = None,
    column_mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Export view data to CSV file, S3, email, or another dataset.

    Args:
        view_id: The dataview ID to export from.
        format: Export format — one of: csv, s3, email, dataset.
        dataset_id: The dataset ID (auto-detected if not provided).
        file_name: (s3) Output filename (auto-generated if not provided).
        file_type: (s3) File format (default "csv").
        recipients: (email) List of email addresses.
        dest_dataset_id: (dataset) Target dataset ID for branch-out.
        column_mapping: (dataset) Column mapping dict (optional).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    fmt = format.lower()

    if fmt == "csv":
        path = await run_sync(view.export.to_csv)
        return success_response({"file_path": str(path)}, f"Exported to {path}")

    elif fmt == "s3":
        result = await run_sync(view.export.to_s3, file_name=file_name, file_type=file_type)
        return success_response(result, "Exported to S3")

    elif fmt == "email":
        if not recipients:
            raise ValueError("recipients is required for email export")
        result = await run_sync(view.export.to_email, recipients=recipients)
        return success_response(result, f"Emailed to {', '.join(recipients)}")

    elif fmt == "dataset":
        if not dest_dataset_id:
            raise ValueError("dest_dataset_id is required for dataset export")
        result = await run_sync(view.export.to_dataset, dest_dataset_id, column_mapping)
        return success_response(result, f"Branched out to dataset {dest_dataset_id}")

    else:
        raise ValueError(f"Unknown format '{format}'. Use: csv, s3, email, dataset")


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
    # General
    dataset_id: int | None = None,
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
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    db = db_type.lower()

    if db == "postgres":
        if not all([host, port, database, table, username, password]):
            raise ValueError("host, port, database, table, username, password are all required for postgres")
        result = await run_sync(
            view.export.to_postgres,
            host=host, port=port, database=database,
            table=table, username=username, password=password,
        )

    elif db == "mysql":
        if not all([host, port, database, table, username, password]):
            raise ValueError("host, port, database, table, username, password are all required for mysql")
        result = await run_sync(
            view.export.to_mysql,
            host=host, port=port, database=database,
            table=table, username=username, password=password,
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
            raise ValueError("host, port, database, table, username, password are all required for redshift")
        result = await run_sync(
            view.export.to_redshift,
            host=host, port=port, database=database,
            table=table, username=username, password=password,
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
        raise ValueError(f"Unknown db_type '{db_type}'. Use: postgres, mysql, bigquery, redshift, elasticsearch")

    return success_response(result, f"Exported to {db_type}")
