"""Organization tools — folders, projects, datasets, users, and bulk operations."""

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

# ── Folders ──────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def list_folders(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List all folders in the workspace.

    Args:
        limit: Maximum number of folders to return (default 50).
        offset: Number of folders to skip for pagination.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.folders.list, limit=limit, offset=offset)
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, "Listed folders")


@mcp.tool()
@log_tool_call
@handle_errors
async def create_folder(
    ctx: Context,
    name: str,
    parent_resource_id: str | None = None,
) -> dict[str, Any]:
    """Create a new folder for organizing datasets and files.

    Args:
        name: Folder name.
        parent_resource_id: Optional parent folder resource ID for nesting.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.folders.create, name, parent_resource_id=parent_resource_id
    )
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, f"Created folder '{name}'")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_folder(
    ctx: Context,
    folder_ids: list[int],
    remove_contents: bool = True,
) -> dict[str, Any]:
    """Delete one or more folders.

    Args:
        folder_ids: List of folder IDs to delete.
        remove_contents: Also delete folder contents (default true).
    """
    manager = await get_manager(ctx)
    await run_sync(manager.client.folders.delete, folder_ids, remove_contents=remove_contents)
    return success_response(message=f"Deleted {len(folder_ids)} folder(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def move_to_folder(
    ctx: Context,
    resource_ids: list[str],
    target_folder_resource_id: str | None = None,
) -> dict[str, Any]:
    """Move resources (datasets, files) into a folder.

    Args:
        resource_ids: List of resource IDs to move.
        target_folder_resource_id: Destination folder resource ID (None for root).
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.folders.move,
        resource_ids,
        target_folder_resource_id=target_folder_resource_id,
    )
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, f"Moved {len(resource_ids)} resource(s)")


# ── Projects ─────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def get_project(ctx: Context, project_id: int) -> dict[str, Any]:
    """Get details of a specific project.

    Args:
        project_id: The project ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.projects.get, project_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def create_project(
    ctx: Context,
    name: str,
    color: str | None = None,
) -> dict[str, Any]:
    """Create a new project in the workspace.

    Args:
        name: Project name.
        color: Optional project color (hex code).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.projects.create, name, color=color)
    return success_response(result, f"Created project '{name}'")


@mcp.tool()
@log_tool_call
@handle_errors
async def update_project(
    ctx: Context,
    project_id: int,
    name: str | None = None,
    color: str | None = None,
) -> dict[str, Any]:
    """Update an existing project's name or color.

    Args:
        project_id: The project ID.
        name: New project name.
        color: New project color (hex code).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.projects.update, project_id, name=name, color=color)
    return success_response(result, f"Updated project {project_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_project(ctx: Context, project_id: int) -> dict[str, Any]:
    """Delete a project and all its contents permanently.

    Args:
        project_id: The project ID to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.projects.delete, project_id)
    return success_response(result, f"Deleted project {project_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def add_project_users(
    ctx: Context,
    project_id: int,
    user_ids: list[str],
    role: str | None = None,
) -> dict[str, Any]:
    """Add users to a project with an optional role.

    Args:
        project_id: The project ID.
        user_ids: List of user IDs to add.
        role: Optional role for the users.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.projects.add_users, project_id, user_ids, role=role)
    return success_response(result, f"Added {len(user_ids)} user(s) to project {project_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def remove_project_users(
    ctx: Context,
    project_id: int,
    user_ids: list[str],
) -> dict[str, Any]:
    """Remove users from a project.

    Args:
        project_id: The project ID.
        user_ids: List of user IDs to remove.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.projects.remove_users, project_id, user_ids)
    return success_response(result, f"Removed {len(user_ids)} user(s) from project {project_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def browse_project(ctx: Context, project_id: int) -> dict[str, Any]:
    """Browse a project's contents (datasets, views, folders).

    Args:
        project_id: The project ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.projects.browse, project_id)
    return success_response(result)


# ── Datasets ─────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def create_dataset(
    ctx: Context,
    dataset_spec: dict[str, Any],
    ds_creation_type: str,
    folder_resource_id: str | None = None,
) -> dict[str, Any]:
    """Create a new dataset programmatically.

    Args:
        dataset_spec: Dataset specification (name, columns, etc.).
        ds_creation_type: Creation type (e.g. "api", "upload").
        folder_resource_id: Optional folder to place the dataset in.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.datasets.create,
        dataset_spec,
        ds_creation_type,
        folder_resource_id=folder_resource_id,
    )
    return success_response(result, "Created dataset")


@mcp.tool()
@log_tool_call
@handle_errors
async def update_dataset(
    ctx: Context,
    dataset_id: int,
    patch_data: dict[str, Any],
) -> dict[str, Any]:
    """Update a dataset's metadata.

    Args:
        dataset_id: The dataset ID.
        patch_data: Fields to update (name, description, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.datasets.update, dataset_id, patch_data)
    return success_response(result, f"Updated dataset {dataset_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_dataset(ctx: Context, dataset_id: int) -> dict[str, Any]:
    """Delete a dataset and all its views permanently.

    Args:
        dataset_id: The dataset ID to delete.
    """
    manager = await get_manager(ctx)
    await run_sync(manager.client.datasets.delete, dataset_id)
    return success_response(message=f"Deleted dataset {dataset_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def browse_dataset(ctx: Context, dataset_id: int) -> dict[str, Any]:
    """Browse a dataset's contents (views, batches, file settings).

    Args:
        dataset_id: The dataset ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.datasets.browse, dataset_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def get_file_settings(ctx: Context, dataset_id: int) -> dict[str, Any]:
    """Get the file-level settings for a dataset (delimiter, encoding, etc.).

    Args:
        dataset_id: The dataset ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.datasets.get_file_settings, dataset_id)
    return success_response(result)


# ── Views (bulk operations) ──────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def bulk_delete_views(
    ctx: Context,
    view_ids: list[int],
) -> dict[str, Any]:
    """Delete multiple views at once.

    Args:
        view_ids: List of view IDs to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dataviews.bulk_delete, view_ids)
    return success_response(result, f"Deleted {len(view_ids)} view(s)")
