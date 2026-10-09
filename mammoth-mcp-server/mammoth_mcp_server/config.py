"""What this deployment is: its URLs, the Mammoth API it calls, and its store.

Every value comes from the environment, so one build runs anywhere. The server
names no Mammoth code but the SDK: it reaches Mammoth through the API alone.
"""

import os
from urllib.parse import urlparse


def read(name: str, default: str) -> str:
    """One setting from the environment, or its default when it is not set."""
    return os.environ.get(name) or default


# The web app, as a user's browser reaches it.
APP_URL = read("MAMMOTH_APP_URL", "https://app.mammoth.io").rstrip("/")
# The host that serves a published dashboard.
DASHBOARD_DOMAIN = read("MAMMOTH_DASHBOARD_URL", APP_URL).rstrip("/")

# The Mammoth API every tool call is sent to, as the SDK takes it.
API_URL = read("MAMMOTH_API_URL", f"{APP_URL}/api/v2").rstrip("/")
# The path the API is served under. Empty for a server that is reached
# directly, which mounts its routes at their own paths.
API_ROOT: str | None = os.environ.get("MAMMOTH_API_ROOT", "/api/v2") or None

# This server, as a client reaches it. The canonical MCP server URI (RFC 8707)
# is this URL plus `/mcp`: a client asks for a token for it.
SERVER_URL = read("MCP_SERVER_URL", "https://mcp.mammoth.io").rstrip("/")
MCP_PATH = "/mcp"
MCP_RESOURCE_URL = f"{SERVER_URL}{MCP_PATH}"
# Where a person reads about Mammoth, for the server card.
DOCS_URL = "https://docs.mammoth.io"
# The authorization server that signs users in for this server: Mammoth's own,
# which the API serves. A client is sent there, and a token it issues for
# `MCP_RESOURCE_URL` is the one bearer this server takes.
MCP_OAUTH_URL = read("MAMMOTH_OAUTH_URL", f"{APP_URL}/api/v2").rstrip("/")
# The upload page, as the user's browser reaches it. A tool hands out this URL
# with a ticket.
MCP_UPLOAD_PATH = "/upload"
MCP_UPLOAD_URL = f"{SERVER_URL}{MCP_UPLOAD_PATH}"
# The origin of the upload page: the host lets the in-chat uploader's frame
# fetch only from the origins its resource names.
UPLOAD_ORIGIN = "{0.scheme}://{0.netloc}".format(urlparse(MCP_UPLOAD_URL))

# Where upload tickets are kept, and the key the caller's token in one is
# sealed with. Generate the key with
# `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
REDIS_URL = read("MCP_REDIS_URL", "redis://localhost:6379/0")
ENCRYPTION_KEY = read("MCP_ENCRYPTION_KEY", "")
# Keeps this server's records apart from another deployment's in one Redis.
STORE_PREFIX = read("MCP_STORE_PREFIX", "mammoth_mcp")

HOST = read("MCP_HOST", "127.0.0.1")
PORT = int(read("MCP_PORT", "8270"))
