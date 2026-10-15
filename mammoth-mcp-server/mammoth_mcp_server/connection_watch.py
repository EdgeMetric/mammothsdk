"""The watch for the connection a user makes in Mammoth after `connect_source`.

A connection is new when its key was not there when the link was handed over,
so the watch keeps the keys there were then. It lives in the store, not in the
model's context: the model passes one `watch_id`, never a list of keys to copy.
"""

import secrets
import time

from .consts import CONNECT_WATCH_SECONDS, ConnectionFields, ConnectorFields
from .sdk import JsonValue, build_client, read_sdk_errors
from .store import Record, recall, remember

# Kept a minute past the watch, so a call that starts at its end still reads it.
KEPT_SECONDS = CONNECT_WATCH_SECONDS + 60


async def list_connections_to(
    workspace_id: int, project_id: int, connector_key: str
) -> list[dict[str, JsonValue]]:
    """The project's connections to one connector."""
    async with build_client(workspace_id, project_id) as client:
        listed = await read_sdk_errors(
            client.connectors.list_connections(connector_key, project_id=project_id)
        )
    return [one for one in listed if isinstance(one, dict)]


async def start_watch(workspace_id: int, project_id: int, connector_key: str) -> str:
    """Note the connections there are now, and return the id to watch for a new one with."""
    known = await list_connections_to(workspace_id, project_id, connector_key)
    watch_id = secrets.token_urlsafe(16)
    await remember(
        ConnectorFields.WATCH,
        watch_id,
        {
            ConnectorFields.WORKSPACE_ID: workspace_id,
            ConnectorFields.PROJECT_ID_KEY: project_id,
            ConnectorFields.CONNECTOR: connector_key,
            ConnectorFields.KNOWN: [one.get(ConnectionFields.CONNECTION_KEY) for one in known],
            ConnectorFields.STARTED: time.time(),
        },
        KEPT_SECONDS,
    )
    return watch_id


async def read_watch(watch_id: str) -> Record | None:
    """The watch, or None once it is gone."""
    return await recall(ConnectorFields.WATCH, watch_id)
