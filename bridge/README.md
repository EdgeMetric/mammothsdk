# Mammoth SDK HTTP Bridge

A thin local HTTP server that proxies JSON requests from browser artifacts to the Mammoth Python SDK, adding CORS headers so browser JavaScript can call the SDK without hitting cross-origin restrictions.

## Setup

```bash
# From the repo root
poetry install --with bridge
# or
pip install -e ".[bridge]"
```

## Configuration

Create `bridge/.env`:

```env
MAMMOTH_API_KEY=your-api-key
MAMMOTH_API_SECRET=your-api-secret
MAMMOTH_WORKSPACE_ID=304
MAMMOTH_PROJECT_ID=1134
MAMMOTH_BASE_URL=https://app.mammoth.io/api/v2
```

All values can also be passed as CLI args (run `python bridge/main.py --help`).

## Running

```bash
python bridge/main.py
# Mammoth bridge listening on http://127.0.0.1:5555
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Connection test (`{"ok": true}`) |
| `GET` | `/methods` | List all available SDK methods |
| `POST` | `/rpc` | Dispatch an SDK method call |

## Request format

```json
{
  "method": "view.filter_rows",
  "view_id": 1039,
  "args": {
    "condition": {"column": "Sales", "operator": "GTE", "value": 1000},
    "filter_type": "SHOW"
  }
}
```

**Method namespaces**: `view.<method>`, `view.export.<method>`, `views.<method>`, `client.<method>`, `client.<sub>.<method>`.

## Response format

```json
{"ok": true, "result": {...}}
{"ok": false, "error": "MammothColumnError", "message": "Column 'X' not found..."}
```

## Condition syntax

```json
{"column": "Sales", "operator": "GTE", "value": 1000}
{"and": [{"column": "Sales", "operator": "GTE", "value": 1000}, {"column": "Region", "operator": "EQ", "value": "West"}]}
{"or": [...]}
{"not": {"column": "Status", "operator": "EQ", "value": "Closed"}}
```

## Usage from a browser artifact

```js
const BRIDGE = "http://localhost:5555";

const res = await fetch(`${BRIDGE}/rpc`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({
    method: "view.data",
    view_id: 1039,
    args: {limit: 10}
  })
});
const {ok, result, error, message} = await res.json();
```
