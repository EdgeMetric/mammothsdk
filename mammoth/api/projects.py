"""
Projects API client for managing projects in Mammoth.
"""

from typing import Optional, Dict, Any, Union, List


class ProjectsAPI:
    """Client for interacting with Mammoth Projects API."""
    
    def __init__(self, client):
        self._client = client
    
    def list_projects(
        self,
        workspace_id: Optional[int] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List all projects in a workspace.
        
        Args:
            workspace_id: ID of the workspace (auto-detected if not provided)
            limit: Maximum number of results (default: 100)
            
        Returns:
            Dict containing projects with id and name
            
        Raises:
            MammothAPIError: If the API request fails
        """
        if workspace_id is None:
            workspace_id = self._client.get_workspace_id()
            if workspace_id is None:
                raise ValueError("Unable to determine workspace ID from API credentials")
        
        params = {
            "fields": "id,name",
            "limit": limit
        }
            
        response = self._client._request(
            "GET",
            f"/workspaces/{workspace_id}/projects",
            params=params
        )
        return response
    
    def get_project(
        self,
        project: Union[int, str, None] = None,
        workspace_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get a single project by ID, name, or auto-selection.
        
        Behavior:
        - project=None: Auto-select if only 1 project exists, otherwise show list and ask user to choose
        - project=123: Find project with ID 123
        - project="My Project": Find project with name "My Project"
        
        Examples:
            # Auto-select if only 1 project exists
            project = client.projects.get_project()
            
            # Get project by ID
            project = client.projects.get_project(project=123)
            
            # Get project by name  
            project = client.projects.get_project(project="My Project")
        
        Args:
            project: Project ID (int), project name (str), or None for auto-selection
            workspace_id: ID of the workspace (auto-detected if not provided)
            
        Returns:
            Dict: Complete project information with id, name, and other fields
            
        Raises:
            ValueError: If project cannot be found or multiple projects exist without specification
            MammothAPIError: If the API request fails
        """
        # Get all projects to work with
        projects_response = self.list_projects(workspace_id=workspace_id)
        projects = projects_response.get('projects', [])
        
        if not projects:
            raise ValueError("No projects found in workspace")
        
        if isinstance(project, int):
            # Find project by ID
            matching_projects = [p for p in projects if p['id'] == project]
            if not matching_projects:
                available_projects = [(p['name'], p['id']) for p in projects]
                raise ValueError(f"Project ID {project} not found. Available projects: {available_projects}")
            return {"id": matching_projects[0]['id'], "name": matching_projects[0]['name']}
        
        if project is None:
            # Auto-selection: use if only 1 project exists
            if len(projects) == 1:
                return {"id": projects[0]['id'], "name": projects[0]['name']}
            else:
                project_list = "\n".join([f"  - {p['name']} (ID: {p['id']})" for p in projects])
                raise ValueError(
                    f"Multiple projects found ({len(projects)}). Please specify project by name or ID:\n{project_list}"
                )
        
        if isinstance(project, str):
            # Find project by name
            matching_projects = [p for p in projects if p['name'] == project]
            
            if not matching_projects:
                available_names = [p['name'] for p in projects]
                raise ValueError(f"Project '{project}' not found. Available projects: {available_names}")
            
            if len(matching_projects) > 1:
                project_list = "\n".join([f"  - {p['name']} (ID: {p['id']})" for p in matching_projects])
                raise ValueError(
                    f"Multiple projects found with name '{project}':\n{project_list}\n"
                    "Please specify project by ID instead."
                )
            
            return {"id": matching_projects[0]['id'], "name": matching_projects[0]['name']}
        
        raise ValueError(f"Invalid project type: {type(project)}. Expected int, str, or None")