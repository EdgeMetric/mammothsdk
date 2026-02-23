# Webhooks API Reference

The `WebhooksAPI` manages webhook datasets -- HTTP endpoints that receive data into the Mammoth platform. Webhooks allow external systems to push data directly into Mammoth.

**Access**: `client.webhooks`

## Methods

### list

```python
client.webhooks.list(
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]
```

List webhook datasets in the current project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `50` | Maximum number of results |
| `offset` | `int` | `0` | Number of results to skip |

**Returns**: List of webhook dicts.

```python
webhooks = client.webhooks.list()
for wh in webhooks:
    print(wh["id"], wh.get("name"), wh.get("uri"))
```

### create

```python
client.webhooks.create(
    name: str = "Generic Webhook",
    mode: str | WebhookMode = "replace",
    folder_resource_id: str | None = None,
    origins: str = "*",
    is_secure: bool = False,
) -> dict[str, Any]
```

Create a webhook dataset.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"Generic Webhook"` | Name of the webhook |
| `mode` | `str \| WebhookMode` | `"replace"` | `"replace"` (overwrite on each push) or `"combine"` (append) |
| `folder_resource_id` | `str \| None` | `None` | Folder to place the webhook in |
| `origins` | `str` | `"*"` | Allowed CORS origins |
| `is_secure` | `bool` | `False` | Generate a secret for authentication |

**Returns**: Dict with created webhook info including the `uri` for sending data.

```python
from mammoth.models.webhooks import WebhookMode

wh = client.webhooks.create(
    name="Sales Events",
    mode=WebhookMode.COMBINE,
    is_secure=True,
)
print(wh["uri"])  # Use this URI to send data
```

### get

```python
client.webhooks.get(
    webhook_id: int,
) -> dict[str, Any]
```

Get webhook details.

### update

```python
client.webhooks.update(
    webhook_id: int,
    mode: str | WebhookMode | None = None,
    origins: str | None = None,
    is_secure: bool | None = None,
) -> dict[str, Any]
```

Update a webhook using JSON Patch format.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_id` | `int` | *required* | ID of the webhook |
| `mode` | `str \| WebhookMode \| None` | `None` | New data ingestion mode |
| `origins` | `str \| None` | `None` | New allowed CORS origins |
| `is_secure` | `bool \| None` | `None` | Whether the webhook requires a secret |

### delete

```python
client.webhooks.delete(
    webhook_id: int,
) -> dict[str, Any]
```

Delete a webhook.

### send_data

```python
client.webhooks.send_data(
    webhook_uri: str,
    data: dict[str, Any],
) -> dict[str, Any]
```

Send data to a webhook via POST.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_uri` | `str` | *required* | Webhook URI path (e.g. `"nHC1zIl97JzgDMopgcfpOgLV"`) |
| `data` | `dict` | *required* | Data payload to send |

```python
client.webhooks.send_data("nHC1zIl97JzgDMopgcfpOgLV", {
    "sale_id": 1001,
    "amount": 250.00,
    "region": "West",
})
```

### send_data_get

```python
client.webhooks.send_data_get(
    webhook_uri: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]
```

Send data to a webhook via GET query parameters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_uri` | `str` | *required* | Webhook URI path |
| `params` | `dict \| None` | `None` | Data as query parameters |

## See also

- [Files](files.md) -- File-based data import
- [Connectors](connectors.md) -- Database connector import
