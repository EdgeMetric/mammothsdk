"""The ``link`` command: local, read-only, turns a pasted Mammoth app URL into ids.

A user pastes a link from the web app (``.../workspaces/W/projects/P/data/folders/F
?selectedResourceId=R``, a dataset or view editor link, a dashboard link) and asks
about the item behind it. Every id in the link is already there, so reading it
needs no server; ``link`` is the one place that knows the app's route shapes, so
an agent does not guess which number is which.

The route shapes mirror the web app's router (mm-frontend ``data-library``,
``data-editor``, ``workflows``, ``dashboard`` and ``data-apps`` route files).
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError
from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]

#: ``(pattern, field)``: each pattern captures one id out of the URL path.
_PATH_IDS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"/workspaces/(\d+)(?:/|$)"), "workspace_id"),
    (re.compile(r"/projects/(\d+)(?:/|$)"), "project_id"),
    (re.compile(r"/data/folders/(\d+)(?:/|$)"), "folder_resource_id"),
    (re.compile(r"/datasets/(\d+)(?:/|$)"), "dataset_id"),
    (re.compile(r"/(?:views|dataviews)/(\d+)(?:/|$)"), "view_id"),
    (re.compile(r"/dashboard/(\d+)(?:/|$)"), "dashboard_id"),
    (re.compile(r"/data-apps/(\d+)(?:/|$)"), "data_app_id"),
    (re.compile(r"/workflows/(\d+)(?:/|$)"), "workflow_id"),
)

#: Resource ids differ from dataset/view ids; said whenever the link carries one.
_RESOURCE_ID_NOTE = (
    "folder_resource_id and selected_resource_id are the web app's resource ids, not "
    "dataset or view ids: never pass them as DATASET_ID or VIEW_ID. Find the item "
    "with 'mammoth dataset find NAME' or 'mammoth dataset list --project PROJECT_ID'."
)


def _parse_error(url: str) -> CliError:
    return CliError(
        code=CODE_INVALID_ARGUMENT,
        message=f"{url!r} is not a Mammoth app link (no /workspaces/ID in its path).",
        exit_status=EXIT_USAGE,
        hint="Paste the full address from the browser, for example "
        "https://app.mammoth.io/workspaces/1/projects/2/data/datasets.",
    )


def parse_app_link(url: str) -> dict[str, Any]:
    """Ids carried by one Mammoth app URL; absent ones are left out. Pure, no network."""
    parsed = urlparse(url.strip())
    path = parsed.path or ""
    found: dict[str, Any] = {"url": url.strip()}
    for pattern, field in _PATH_IDS:
        match = pattern.search(path)
        if match is not None:
            found[field] = int(match.group(1))
    if "workspace_id" not in found:
        raise _parse_error(url)
    query = parse_qs(parsed.query)
    for key, field in (("selectedResourceId", "selected_resource_id"), ("openSection", "section")):
        if query.get(key):
            value = query[key][0]
            found[field] = int(value) if value.isdigit() else value
    if "folder_resource_id" in found or "selected_resource_id" in found:
        found["note"] = _RESOURCE_ID_NOTE
    return found


def link(invocation: Invocation) -> HandlerResult:
    """Read the workspace, project, folder, dataset and view ids out of a pasted app URL.

    The sole positional argument is the URL. Returns only the ids the link
    carries; makes no request.
    """
    url = invocation.extra_args[0] if invocation.extra_args else None
    if not url or not url.strip():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="link requires a Mammoth app URL argument.",
            exit_status=EXIT_USAGE,
            hint="Pass the pasted link in quotes: mammoth link 'https://app.mammoth.io/...'.",
        )
    return parse_app_link(url), {}
