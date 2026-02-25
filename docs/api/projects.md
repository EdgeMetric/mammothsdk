# Projects API Reference

The `ProjectsAPI` manages projects within a workspace. Projects are siloed areas for organizing datasets, views, and pipelines.

**Access**: `client.projects`

## Methods

### list

```python
client.projects.list(
    workspace_id: int | None = None,
    limit: int = 100,
) -> dict[str, Any]
```

List all projects in a workspace.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default if not provided) |
| `limit` | `int` | `100` | Maximum number of results |

**Returns**: Dict containing `projects` list with `id` and `name` fields.

```python
resp = client.projects.list()
for p in resp["projects"]:
    print(p["id"], p["name"])
```

### get

```python
client.projects.get(
    project: int | str | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Get a single project by ID, name, or auto-selection.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project` | `int \| str \| None` | `None` | Project ID (int), name (str), or None for auto-selection |
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default if not provided) |

**Behavior**:

- `project=None` -- auto-selects if only one project exists
- `project=123` -- finds project by ID
- `project="My Project"` -- finds project by name

**Returns**: Dict with `id` and `name`.

**Raises**: `ValueError` if project not found or ambiguous.

```python
# By ID
project = client.projects.get(123)

# By name
project = client.projects.get("Analytics")

# Auto-select (only works if workspace has exactly one project)
project = client.projects.get()
```

### create

```python
client.projects.create(
    name: str,
    color: str | None = None,
    project_access: str | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Create a new project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Name for the new project |
| `color` | `str \| None` | `None` | Color hex code (e.g., `"#337FBD"`) |
| `project_access` | `str \| None` | `None` | `"only_me"`, `"some_members_of_workspace"`, or `"all_members_of_workspace"` |
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default if not provided) |

```python
project = client.projects.create(name="Q4 Analytics", color="#3498db")
print(project["id"])
```

### update

```python
client.projects.update(
    project_id: int,
    name: str | None = None,
    color: str | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Update a project's name or color.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | `int` | *required* | ID of the project to update |
| `name` | `str \| None` | `None` | New name |
| `color` | `str \| None` | `None` | New color code |
| `workspace_id` | `int \| None` | `None` | Workspace ID |

```python
client.projects.update(123, name="Q4 Analytics v2")
```

### delete

```python
client.projects.delete(
    project_id: int,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Delete a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | `int` | *required* | ID of the project to delete |
| `workspace_id` | `int \| None` | `None` | Workspace ID |

### bulk_update

```python
client.projects.bulk_update(
    patch_data: dict[str, Any],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Bulk update multiple projects using JSON Patch operations.

### bulk_delete

```python
client.projects.bulk_delete(
    project_ids: list[int],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Bulk delete multiple projects.

```python
client.projects.bulk_delete([101, 102, 103])
```

### add_users

```python
client.projects.add_users(
    project_id: int,
    user_ids: list[str],
    role: str | None = None,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Add users to a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | `int` | *required* | ID of the project |
| `user_ids` | `list[str]` | *required* | User email addresses or IDs |
| `role` | `str \| None` | `None` | Role to assign |

```python
client.projects.add_users(123, ["user@example.com"], role="editor")
```

### remove_users

```python
client.projects.remove_users(
    project_id: int,
    user_ids: list[str],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Remove users from a project.

### browse

```python
client.projects.browse(
    project_id: int,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Browse project contents (datasets, folders).

```python
contents = client.projects.browse(123)
```

## See also

- [Client](client.md) -- MammothClient and sub-clients overview
- [Datasets](datasets.md) -- Dataset management within projects
