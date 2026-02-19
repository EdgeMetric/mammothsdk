"""Export tools — CSV, S3, email, database exports."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth.exceptions import MammothAPIError, MammothColumnError
from mammoth_mcp.helpers import error_response, get_manager, success_response
from mammoth_mcp.server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
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
    try:
        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        fmt = format.lower()

        if fmt == "csv":
            path = view.export.to_csv()
            return success_response({"file_path": str(path)}, f"Exported to {path}")

        elif fmt == "s3":
            result = view.export.to_s3(file_name=file_name, file_type=file_type)
            return success_response(result, "Exported to S3")

        elif fmt == "email":
            if not recipients:
                return error_response(ValueError("recipients is required for email export"))
            result = view.export.to_email(recipients=recipients)
            return success_response(result, f"Emailed to {', '.join(recipients)}")

        elif fmt == "dataset":
            if not dest_dataset_id:
                return error_response(ValueError("dest_dataset_id is required for dataset export"))
            result = view.export.to_dataset(dest_dataset_id, column_mapping)
            return success_response(result, f"Branched out to dataset {dest_dataset_id}")

        else:
            return error_response(ValueError(f"Unknown format '{format}'. Use: csv, s3, email, dataset"))

    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in export_data")
        return error_response(e)


@mcp.tool()
async def export_to_database(
    ctx: Context,
    view_id: int,
    db_type: str,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    table: str | None = None,
    username: str | None = None,
    password: str | None = None,
    dataset_id: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Export view data to an external database.

    Args:
        view_id: The dataview ID to export from.
        db_type: Database type — one of: postgres, mysql, bigquery, redshift, elasticsearch.
        host: Database host.
        port: Database port.
        database: Database name.
        table: Target table name.
        username: Database username.
        password: Database password.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        db = db_type.lower()

        if db == "postgres":
            if not all([host, port, database, table, username, password]):
                return error_response(ValueError("host, port, database, table, username, password are all required"))
            result = view.export.to_postgres(
                host=host, port=port, database=database,
                table=table, username=username, password=password,
            )

        elif db == "mysql":
            if not all([host, port, database, table, username, password]):
                return error_response(ValueError("host, port, database, table, username, password are all required"))
            result = view.export.to_mysql(
                host=host, port=port, database=database,
                table=table, username=username, password=password,
            )

        elif db == "bigquery":
            result = view.export.to_bigquery(**kwargs)

        elif db == "redshift":
            result = view.export.to_redshift(**kwargs)

        elif db == "elasticsearch":
            result = view.export.to_elasticsearch(**kwargs)

        else:
            return error_response(
                ValueError(f"Unknown db_type '{db_type}'. Use: postgres, mysql, bigquery, redshift, elasticsearch")
            )

        return success_response(result, f"Exported to {db_type}")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in export_to_database")
        return error_response(e)
