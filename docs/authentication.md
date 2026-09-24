# Authentication

The Mammoth SDK authenticates with an API token, sent as `Authorization: Bearer mm_...` on every request.

## Getting an API token

1. Log in to the Mammoth web app
2. Open **Workspace settings → API Tokens** and choose **Create token**
3. Copy the token (it starts with `mm_`); it is shown only once
4. Store it securely; it works only in that workspace and on that server

Older tokens came as an API key and secret. They still work:
`MammothClient(api_key=..., api_secret=..., workspace_id=...)`. Pass either
`api_token` or the pair, not both.

## Client setup

### Direct authentication

```python
from mammoth import MammothClient

client = MammothClient(
    api_token="mm_your-token",
    workspace_id=11,
)
client.set_project_id(10)
```

### Environment variables (recommended)

Store credentials in environment variables for better security:

```bash
export MAMMOTH_API_TOKEN="mm_your-token"
```

```python
import os
from mammoth import MammothClient

client = MammothClient(
    api_token=os.getenv("MAMMOTH_API_TOKEN"),
    workspace_id=11,
)
```

### Configuration file

For projects with multiple environments:

```python
# config.py
import os

MAMMOTH_CONFIG = {
    "api_token": os.getenv("MAMMOTH_API_TOKEN"),
    "workspace_id": int(os.getenv("MAMMOTH_WORKSPACE_ID", "11")),
    "base_url": os.getenv("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
}
```

```python
from mammoth import MammothClient
from config import MAMMOTH_CONFIG

client = MammothClient(**MAMMOTH_CONFIG)
```

## How authentication works

The client adds these headers to every request automatically:

| Header | Value |
|--------|-------|
| `X-API-KEY` | Your API key |
| `X-API-SECRET` | Your API secret |
| `X-WORKSPACE-ID` | Your workspace ID |
| `User-Agent` | `mammoth-io/<version>` |

## Error handling

Authentication errors raise `MammothAuthError` (HTTP 401):

```python
from mammoth import MammothClient, MammothAuthError

try:
    client = MammothClient(
        api_token="mm_invalid",
        workspace_id=1,
    )
    projects = client.projects.list()
except MammothAuthError:
    print("Authentication failed -- check your API credentials")
```

## Security best practices

**Never hardcode credentials** -- use environment variables or a secrets manager:

```python
# Do not do this:
client = MammothClient(api_key="pk_live_123456789", ...)

# Do this instead:
client = MammothClient(api_key=os.getenv("MAMMOTH_API_KEY"), ...)
```

**Use different credentials per environment** -- separate dev, staging, and production keys.

**Rotate credentials regularly** -- regenerate API keys periodically and invalidate old ones.

**Do not commit credentials** -- add `.env` and config files with secrets to `.gitignore`.

**Use HTTPS API endpoints** -- the client rejects non-HTTPS API base URLs by
default. Local HTTP development requires the explicit
`allow_insecure_loopback_http=True` opt-in and is restricted to loopback hosts.

## Next steps

- [Quick Start Guide](quick-start.md)
- [Client API Reference](api/client.md)
