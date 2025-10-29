"""
Helper utilities for the Mammoth Analytics SDK.
"""

from typing import Dict, Optional
import re


def parse_path(url: str) -> Dict[str, Optional[int]]:
    """
    Parse Mammoth URL to extract workspace, project, folder, and dataview IDs.
    
    Args:
        url: Mammoth URL
        
    Returns:
        Dict with keys: workspace_id, project_id, folder_id, dataview_id
        
    Examples:
        parse_path("https://mirai.mammoth.io/#/workspaces/11/projects/98/views/1039")
        # Returns: {"workspace_id": 11, "project_id": 98, "folder_id": None, "dataview_id": 1039}
        
        parse_path("https://mirai.mammoth.io/#/workspaces/11/projects/98")
        # Returns: {"workspace_id": 11, "project_id": 98, "folder_id": None, "dataview_id": None}
        
        parse_path("http://mirai.mammoth.io/#/workspaces/11/projects/98/folders/2546")
        # Returns: {"workspace_id": 11, "project_id": 98, "folder_id": 2546, "dataview_id": None}
    """
    result = {
        "workspace_id": None,
        "project_id": None, 
        "folder_id": None,
        "dataview_id": None
    }
    
    # Extract workspace ID
    workspace_match = re.search(r'/workspaces/(\d+)', url)
    if workspace_match:
        result["workspace_id"] = int(workspace_match.group(1))
    
    # Extract project ID
    project_match = re.search(r'/projects/(\d+)', url)
    if project_match:
        result["project_id"] = int(project_match.group(1))
    
    # Extract folder ID
    folder_match = re.search(r'/folders/(\d+)', url)
    if folder_match:
        result["folder_id"] = int(folder_match.group(1))
    

    dataview_match = re.search(r'/(?:views)/(\d+)', url)
    if dataview_match:
        result["dataview_id"] = int(dataview_match.group(1))
    
    # Filter out None values
    return {k: v for k, v in result.items() if v is not None}