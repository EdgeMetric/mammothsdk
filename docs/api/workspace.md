# Workspace & Users API Reference

The SDK provides two sub-clients for workspace and user management:

- **`client.workspaces`** (`WorkspaceAPI`) -- workspace CRUD and user management
- **`client.user_profile`** (`UserProfileAPI`) -- current user profile and preferences

## WorkspaceAPI

**Access**: `client.workspaces`

### list

```python
client.workspaces.list(
    limit: int = 100,
) -> dict[str, Any]
```

List all accessible workspaces.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `100` | Maximum number of results |

**Returns**: Dict containing `workspaces` list with `id` and `name`.

```python
resp = client.workspaces.list()
for ws in resp.get("workspaces", []):
    print(ws["id"], ws["name"])
```

### get

```python
client.workspaces.get(
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Get details of a specific workspace.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workspace_id` | `int \| None` | `None` | Workspace ID (uses client default if not provided) |

### update

```python
client.workspaces.update(
    config: dict[str, Any],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Update workspace settings.

### delete

```python
client.workspaces.delete(
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Delete a workspace.

### reactivate

```python
client.workspaces.reactivate(
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Reactivate a deactivated workspace.

### list_users

```python
client.workspaces.list_users(
    workspace_id: int | None = None,
) -> list[dict[str, Any]]
```

List all users in a workspace.

**Returns**: List of user dicts.

```python
users = client.workspaces.list_users()
for u in users:
    print(u.get("email"), u.get("role"))
```

### get_user

```python
client.workspaces.get_user(
    user_id: str,
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Get details of a specific user.

### update_user

```python
client.workspaces.update_user(
    user_id: str,
    config: dict[str, Any],
    workspace_id: int | None = None,
) -> dict[str, Any]
```

Update a user's settings in the workspace.

---

## UserProfileAPI

**Access**: `client.user_profile`

Manages the current authenticated user's profile and preferences.

### get

```python
client.user_profile.get() -> dict[str, Any]
```

Get the current user's profile information.

```python
profile = client.user_profile.get()
print(profile.get("name"), profile.get("email"))
```

### update

```python
client.user_profile.update(**fields: Any) -> dict[str, Any]
```

Update the current user's profile.

| Parameter | Type | Description |
|-----------|------|-------------|
| `**fields` | `Any` | Profile fields to update (name, email, etc.) |

```python
client.user_profile.update(name="Jane Doe")
```

### change_password

```python
client.user_profile.change_password(
    current_password: str,
    new_password: str,
) -> dict[str, Any]
```

Change the current user's password.

| Parameter | Type | Description |
|-----------|------|-------------|
| `current_password` | `str` | Current password |
| `new_password` | `str` | New password |

### get_preferences

```python
client.user_profile.get_preferences() -> dict[str, Any]
```

Get user preferences (UI settings, notifications, etc.).

### update_preferences

```python
client.user_profile.update_preferences(**prefs: Any) -> dict[str, Any]
```

Update user preferences.

## See also

- [Projects](projects.md) -- Project management within workspaces
- [Authentication](../authentication.md) -- API credentials setup
- [Client](client.md) -- MammothClient overview
