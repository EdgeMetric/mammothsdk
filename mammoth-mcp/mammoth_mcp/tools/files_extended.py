"""Extended file tools — list, inspect, delete, and manage uploaded files."""

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
async def list_files(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List uploaded files in the workspace.

    Args:
        limit: Maximum number of files to return (default 50).
        offset: Number of files to skip for pagination.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.files.list, limit=limit, offset=offset)
    # FilesList is a pydantic model — convert to dict
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, "Listed files")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_file(ctx: Context, file_id: int) -> dict[str, Any]:
    """Get details of a specific uploaded file.

    Args:
        file_id: The file ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.files.get, file_id)
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data)


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_file(ctx: Context, file_id: int) -> dict[str, Any]:
    """Delete an uploaded file permanently.

    Args:
        file_id: The file ID to delete.
    """
    manager = await get_manager(ctx)
    await run_sync(manager.client.files.delete, file_id)
    return success_response(message=f"Deleted file {file_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def extract_sheets(
    ctx: Context,
    file_id: int,
    sheets: list[str],
    delete_file_after_extract: bool = True,
    combine_after_extract: bool = False,
) -> dict[str, Any]:
    """Extract specific sheets from an uploaded Excel file into separate datasets.

    Args:
        file_id: The Excel file ID.
        sheets: List of sheet names to extract.
        delete_file_after_extract: Delete the original file after extraction (default true).
        combine_after_extract: Combine extracted sheets into one dataset (default false).
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.files.extract_sheets,
        file_id,
        sheets,
        delete_file_after_extract=delete_file_after_extract,
        combine_after_extract=combine_after_extract,
    )
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, f"Extracted {len(sheets)} sheet(s) from file {file_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def set_file_password(
    ctx: Context,
    file_id: int,
    password: str,
) -> dict[str, Any]:
    """Set a password on a password-protected uploaded file to unlock processing.

    SECURITY NOTE: The password is passed through the LLM context. For sensitive
    files, consider using the Mammoth UI directly.

    Args:
        file_id: The file ID.
        password: The file password.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.files.set_password, file_id, password)
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, f"Set password for file {file_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def upload_folder(
    ctx: Context,
    folder_path: str,
    folder_resource_id: str | None = None,
) -> dict[str, Any]:
    """Upload all files in a local folder to Mammoth.

    Args:
        folder_path: Path to the local folder containing files to upload.
        folder_resource_id: Optional Mammoth folder to upload into.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.files.upload_folder,
        folder_path,
        folder_resource_id=folder_resource_id,
    )
    return success_response(result, f"Uploaded folder '{folder_path}'")
