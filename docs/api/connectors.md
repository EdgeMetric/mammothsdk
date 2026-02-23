# Connectors API Reference

The `ConnectorsAPI` manages cloud data source connectors and their connections. Use connectors to import data from databases (PostgreSQL, MySQL, BigQuery, etc.), cloud storage, and other external sources.

**Access**: `client.connectors`

## Concepts

- **Connector**: A type of data source (e.g. `"postgres"`, `"mysql"`, `"bigquery"`)
- **Connection**: A configured instance of a connector (host, credentials, etc.)
- **Data source config**: A specific table/query within a connection to import

## Methods

### list

```python
client.connectors.list() -> list[dict[str, Any]]
```

List all available connector types.

**Returns**: List of connector dicts with keys like `key`, `name`, `type`.

```python
connectors = client.connectors.list()
for c in connectors:
    print(c["key"], c["name"])
```

### get

```python
client.connectors.get(
    connector_key: str,
) -> dict[str, Any]
```

Get details of a specific connector type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connector_key` | `str` | *required* | Connector type key (e.g. `"postgres"`, `"mysql"`) |

### active_connectors

```python
client.connectors.active_connectors() -> list[dict[str, Any]]
```

List connectors that have at least one established connection.

### list_connections

```python
client.connectors.list_connections(
    connector_key: str,
    project_id: int | None = None,
) -> list[dict[str, Any]]
```

List connections for a connector type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connector_key` | `str` | *required* | Connector type key |
| `project_id` | `int \| None` | `None` | Project ID (uses client default) |

**Returns**: List of connection dicts.

```python
connections = client.connectors.list_connections("postgres")
for conn in connections:
    print(conn["key"], conn.get("name"))
```

### create_connection

```python
client.connectors.create_connection(
    connector_key: str,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a new connection for a connector.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connector_key` | `str` | *required* | Connector type key |
| `config` | `dict` | *required* | Connection configuration (host, port, database, credentials, etc.) |

```python
conn = client.connectors.create_connection("postgres", {
    "host": "db.example.com",
    "port": 5432,
    "database": "analytics",
    "username": "user",
    "password": "pass",
    "name": "Prod DB",
})
```

### get_connection

```python
client.connectors.get_connection(
    connector_key: str,
    connection_key: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get details of a specific connection.

### update_connection

```python
client.connectors.update_connection(
    connector_key: str,
    connection_key: str,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a connection's configuration.

### delete_connection

```python
client.connectors.delete_connection(
    connector_key: str,
    connection_key: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a connection.

### list_ds_configs

```python
client.connectors.list_ds_configs(
    connector_key: str,
    connection_key: str,
    project_id: int | None = None,
) -> list[dict[str, Any]]
```

List data source configurations for a connection. Each config represents a table, query, or file to import.

### create_ds_config

```python
client.connectors.create_ds_config(
    connector_key: str,
    connection_key: str,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Create a data source configuration to import data from a connection.

### get_ds_config

```python
client.connectors.get_ds_config(
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Get a specific data source configuration.

### update_ds_config

```python
client.connectors.update_ds_config(
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
    config: dict[str, Any],
    project_id: int | None = None,
) -> dict[str, Any]
```

Update a data source configuration.

### delete_ds_config

```python
client.connectors.delete_ds_config(
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
    project_id: int | None = None,
) -> dict[str, Any]
```

Delete a data source configuration.

## See also

- [Files](files.md) -- File-based data import
- [Exports](exports.md) -- Export data to external destinations
- [Client](client.md) -- MammothClient overview
