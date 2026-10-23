"""Which API servers honour ``Idempotency-Key``, remembered between commands.

The SDK sends a fresh ``Idempotency-Key`` on every write and replays a write whose
connection dropped only against a server known to run a keyed write once (it learns
that when a response echoes the key). The SDK forgets it with the process; the CLI is
one process per command, so this file carries it to the next command and its first
write can be replayed too. It holds API base URLs only, owner-only (0600).

An embedded call never touches the disk: the host's process keeps what its SDK learned.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from mammoth import client as sdk_client

from mammoth_cli.manifest.loader import cache_dir
from mammoth_cli.runtime import embedded

_FILE = "idempotency-servers.json"


def _path() -> Path:
    return cache_dir() / _FILE


def _known() -> list[str]:
    try:
        servers = json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(server) for server in servers] if isinstance(servers, list) else []


def recall(base_url: str) -> None:
    """Tell the SDK that ``base_url`` honours keys, when an earlier command learned it.

    Args:
        base_url: The API base URL this command talks to.
    """
    mark = getattr(sdk_client, "mark_idempotency_keys_honoured", None)
    if mark is None or embedded.active():
        return
    if base_url.rstrip("/") in _known():
        mark(base_url)


def remember(base_url: str) -> None:
    """Keep what the SDK learned about ``base_url`` for the next command.

    Args:
        base_url: The API base URL this command talked to.
    """
    honours = getattr(sdk_client, "honours_idempotency_keys", None)
    if honours is None or embedded.active() or not honours(base_url):
        return
    known = _known()
    server = base_url.rstrip("/")
    if server in known:
        return
    path = _path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".idempotency-")
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(sorted({*known, server}), out)
        os.replace(temporary, path)
    except OSError:
        return  # a cache: the next command learns it again
