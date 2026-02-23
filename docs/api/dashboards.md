# Dashboards API Reference

The `DashboardsAPI` manages interactive dashboards in Mammoth. Dashboards visualize data from dataviews and can be shared with team members or embedded externally.

**Access**: `client.dashboards`

## Methods

### list

```python
client.dashboards.list() -> list[dict[str, Any]]
```

List all dashboards accessible to the current user.

**Returns**: List of dashboard dicts.

```python
dashboards = client.dashboards.list()
for d in dashboards:
    print(d["id"], d.get("name"))
```

### create

```python
client.dashboards.create(
    config: dict[str, Any],
) -> dict[str, Any]
```

Create a new dashboard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `dict` | *required* | Dashboard configuration (name, sources, layout, etc.) |

**Returns**: Dict with created dashboard info (may include job ID for async creation).

### get

```python
client.dashboards.get(
    dashboard_id: int,
) -> dict[str, Any]
```

Get dashboard details.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dashboard_id` | `int` | *required* | ID of the dashboard |

### update

```python
client.dashboards.update(
    dashboard_id: int,
    config: dict[str, Any],
) -> dict[str, Any]
```

Update a dashboard configuration.

### delete

```python
client.dashboards.delete(
    dashboard_id: int,
) -> dict[str, Any]
```

Delete a dashboard.

### get_sources

```python
client.dashboards.get_sources() -> list[dict[str, Any]]
```

Get available data sources for dashboard creation.

**Returns**: List of source dicts (dataviews available for charting).

### get_analytics

```python
client.dashboards.get_analytics(
    dashboard_id: int,
) -> dict[str, Any]
```

Get dashboard analytics including view counts and active users.

### share

```python
client.dashboards.share(
    dashboard_id: int,
    config: dict[str, Any],
) -> dict[str, Any]
```

Share a dashboard with users or generate a public link.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dashboard_id` | `int` | *required* | ID of the dashboard |
| `config` | `dict` | *required* | Sharing configuration (users, permissions, etc.) |

### action

```python
client.dashboards.action(
    dashboard_id: int,
    action_config: dict[str, Any],
) -> dict[str, Any]
```

Perform an action on a dashboard (e.g. publish, refresh).

### get_by_url

```python
client.dashboards.get_by_url(
    url: str,
) -> dict[str, Any]
```

Get a dashboard by its URL slug.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | *required* | Dashboard URL slug |

### get_draft_data

```python
client.dashboards.get_draft_data(
    dashboard_id: int,
    sql: str,
) -> dict[str, Any]
```

Query draft dashboard data using SQL.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dashboard_id` | `int` | *required* | ID of the dashboard |
| `sql` | `str` | *required* | SQL query to execute against draft data |

### get_publish_data

```python
client.dashboards.get_publish_data(
    dashboard_id: int,
    sql: str,
) -> dict[str, Any]
```

Query published dashboard data using SQL.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dashboard_id` | `int` | *required* | ID of the dashboard |
| `sql` | `str` | *required* | SQL query to execute against published data |

## See also

- [Views](views.md) -- Data sources for dashboards
- [Exports](exports.md) -- Export data to files and databases
