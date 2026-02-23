# Automations & Schedules API Reference

The SDK provides two sub-clients for automation workflows:

- **`client.automations`** (`AutomationsAPI`) -- manages automations and their associated schedules in a unified interface
- **`client.schedules`** (`SchedulesAPI`) -- manages schedules as a standalone resource

## AutomationsAPI

**Access**: `client.automations`

### Automation methods

#### list

```python
client.automations.list() -> list[dict[str, Any]]
```

List all automations in the current project.

```python
automations = client.automations.list()
for a in automations:
    print(a["id"], a.get("name"))
```

#### create

```python
client.automations.create(
    config: dict[str, Any],
) -> dict[str, Any]
```

Create a new automation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `dict` | *required* | Automation configuration (name, triggers, actions, etc.) |

#### get

```python
client.automations.get(
    automation_id: int,
) -> dict[str, Any]
```

Get automation details.

#### update

```python
client.automations.update(
    automation_id: int,
    config: dict[str, Any],
) -> dict[str, Any]
```

Update an automation.

#### delete

```python
client.automations.delete(
    automation_id: int,
) -> dict[str, Any]
```

Delete an automation.

### Schedule methods (via AutomationsAPI)

#### list_schedules

```python
client.automations.list_schedules() -> list[dict[str, Any]]
```

List all schedules in the current project.

#### create_schedule

```python
client.automations.create_schedule(
    config: dict[str, Any],
) -> dict[str, Any]
```

Create a new schedule.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `dict` | *required* | Schedule configuration (cron, timezone, actions, etc.) |

#### update_schedule

```python
client.automations.update_schedule(
    schedule_id: int,
    config: dict[str, Any],
) -> dict[str, Any]
```

Update a schedule.

#### delete_schedule

```python
client.automations.delete_schedule(
    schedule_id: int,
) -> dict[str, Any]
```

Delete a schedule.

---

## SchedulesAPI

**Access**: `client.schedules`

A standalone sub-client for schedule management with explicit project_id support.

### list

```python
client.schedules.list(
    project_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]
```

List schedules in a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | `int \| None` | `None` | Project ID (uses client default) |
| `limit` | `int` | `50` | Maximum number of results |
| `offset` | `int` | `0` | Number of results to skip |

**Returns**: Dict with `schedules` list and pagination info.

### get

```python
client.schedules.get(
    schedule_id: int,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get schedule details.

### create

```python
client.schedules.create(
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a new schedule.

### update

```python
client.schedules.update(
    schedule_id: int,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a schedule.

### delete

```python
client.schedules.delete(
    schedule_id: int,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a schedule.

## See also

- [Pipeline](pipeline.md) -- Transformation tasks triggered by automations
- [Webhooks](webhooks.md) -- Event-driven data ingestion
