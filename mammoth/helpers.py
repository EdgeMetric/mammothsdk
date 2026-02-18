"""Helper utilities for the Mammoth Analytics SDK.

Provides ``parse_path()`` to extract IDs from Mammoth URLs::

    from mammoth import parse_path

    ids = parse_path("https://app.mammoth.io/#/workspaces/11/projects/98/views/1039")
    # {"workspace_id": 11, "project_id": 98, "dataview_id": 1039}
"""

from __future__ import annotations

import re


def parse_path(url: str) -> dict[str, int]:
    """Parse Mammoth URL to extract workspace, project, folder, and dataview IDs.

    Args:
        url: Mammoth URL.

    Returns:
        Dict with keys: workspace_id, project_id, folder_id, dataview_id.
        Only keys with non-None values are included.

    Examples::

        parse_path("https://mirai.mammoth.io/#/workspaces/11/projects/98/views/1039")
        # Returns: {"workspace_id": 11, "project_id": 98, "dataview_id": 1039}
    """
    result: dict[str, int] = {}

    patterns = {
        "workspace_id": r"/workspaces/(\d+)",
        "project_id": r"/projects/(\d+)",
        "folder_id": r"/folders/(\d+)",
        "dataview_id": r"/(?:views)/(\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, url)
        if match:
            result[key] = int(match.group(1))

    return result
