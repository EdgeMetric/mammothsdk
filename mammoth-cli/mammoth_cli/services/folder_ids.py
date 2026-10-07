"""One folder id: the resource id the web app opens a folder by.

The backend keys a folder two ways: its label id (what ``folder get/update/
delete/trash``, a move target and ``browse folder`` take) and its resource id
(what the app routes by: ``/data/folders/<resource_id>``). The CLI shows and
accepts only the resource id. This module is the one place that translates
between the two, with a single project folder listing per command.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_RESOURCE_NOT_FOUND,
    EXIT_NOT_FOUND,
    CliError,
)

FOLDER_LIST_SYMBOL = "mammoth.api.folders.FoldersAPI.list"
_FOLDER_PAGE = 100
_LABEL_PARENT = re.compile(r"label_(\d+)")
_LABEL_PATH_SEGMENT = re.compile(r"(label:[^:/]*:)(\d+)")
_FOLDER_URL_ID = re.compile(r"(/folders/)(\d+)")


def _dump(value: Any) -> Any:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def _folders_of(page: Any) -> list[dict[str, Any]]:
    """The folder records of a ``FoldersAPI.list`` page (a model or a dict)."""
    page = _dump(page)
    folders = page.get("folders", []) if isinstance(page, dict) else []
    return [f for f in folders if isinstance(f, dict)]


class FolderIds:
    """Translate folder ids for one command; each project is listed at most once."""

    def __init__(self, service: Any) -> None:
        self._service = service
        self._projects: dict[int, list[dict[str, Any]]] = {}

    def _folders(self, project_id: int) -> list[dict[str, Any]]:
        if project_id not in self._projects:
            folders: list[dict[str, Any]] = []
            while True:
                page = self._service.call(
                    FOLDER_LIST_SYMBOL,
                    project_id=project_id,
                    limit=_FOLDER_PAGE,
                    offset=len(folders),
                )
                batch = _folders_of(page)
                folders += batch
                if len(batch) < _FOLDER_PAGE:
                    break
            self._projects[project_id] = folders
        return self._projects[project_id]

    def to_open(self, project_id: int) -> dict[int, int]:
        """``{label id: open id}`` for every folder of the project."""
        return {
            int(f["id"]): int(f["resource_id"])
            for f in self._folders(project_id)
            if f.get("id") is not None and f.get("resource_id") is not None
        }

    def labels(self, project_id: int, open_ids: Iterable[int]) -> list[int]:
        """The label id behind each open id, in order; an unknown id is ``resource_not_found``."""
        by_open = {open_id: label for label, open_id in self.to_open(project_id).items()}
        labels: list[int] = []
        for open_id in open_ids:
            if int(open_id) not in by_open:
                raise CliError(
                    code=CODE_RESOURCE_NOT_FOUND,
                    message=f"No folder with id {open_id} in project {project_id}.",
                    exit_status=EXIT_NOT_FOUND,
                    hint="Use a folder id as 'folder list' shows it.",
                    details={"type": "folder", "id": open_id, "project_id": project_id},
                )
            labels.append(by_open[int(open_id)])
        return labels

    def label(self, project_id: int, open_id: int) -> int:
        return self.labels(project_id, [open_id])[0]

    def open_folder(self, project_id: int, folder: Any) -> Any:
        """A folder record with its open id as ``id``; no ``resource_id`` or label id is left."""
        record = _dump(folder)
        if not isinstance(record, dict) or record.get("resource_id") is None:
            return record  # the project root has no resource id
        to_open = self.to_open(project_id)
        opened = {k: v for k, v in record.items() if k != "resource_id"}
        opened["id"] = int(record["resource_id"])
        parent = _LABEL_PARENT.fullmatch(str(record.get("parent_id") or ""))
        if parent:
            opened["parent_id"] = to_open.get(int(parent.group(1)), record["parent_id"])
        if isinstance(record.get("resource_path"), str):
            opened["resource_path"] = _LABEL_PATH_SEGMENT.sub(
                lambda m: f"{m.group(1)}{to_open.get(int(m.group(2)), m.group(2))}",
                record["resource_path"],
            )
        return opened

    def open_data(self, data: Any, project_id: int | None) -> Any:
        """``data`` with every folder in it shown by its open id.

        A folder is a resource row (``resource_type`` ``label``, as the
        resource routes return it) or a browse tree node (``type`` ``label``);
        the tree names the project each node sits under.
        """
        data = _dump(data)
        if isinstance(data, list):
            return [self.open_data(item, project_id) for item in data]
        if not isinstance(data, dict):
            return data
        if data.get("type") == "project" and isinstance(data.get("id"), int):
            project_id = data["id"]
        if data.get("resource_type") == "label" and data.get("resource_id") is not None:
            return _open_resource_row(data)
        opened = {k: self.open_data(v, project_id) for k, v in data.items()}
        if data.get("type") == "label" and project_id is not None:
            to_open = self.to_open(project_id)
            label = data.get("id")
            if label in to_open:
                opened["id"] = to_open[label]
                if isinstance(data.get("url"), str):
                    opened["url"] = _FOLDER_URL_ID.sub(
                        lambda m: f"{m.group(1)}{to_open[label]}", data["url"]
                    )
        return opened


def _open_resource_row(row: dict[str, Any]) -> dict[str, Any]:
    """A folder resource row with its resource id as ``id``; the tree, object and label ids drop."""
    open_id = int(row["resource_id"])
    opened = {k: v for k, v in row.items() if k not in ("object_id", "resource_id")}
    opened["id"] = open_id
    properties = row.get("object_properties")
    if isinstance(properties, dict):
        opened["object_properties"] = {
            **{k: v for k, v in properties.items() if k != "resource_id"},
            "id": open_id,
        }
    return opened
