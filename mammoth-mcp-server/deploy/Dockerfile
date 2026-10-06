# The Mammoth MCP server as one image, built from this repository.
#
# Built from the repo rather than from PyPI on purpose: the server needs the
# SDK version beside it, so a deployment never waits for a release.
#
# Build it from the REPOSITORY ROOT, which is the build context:
#
#   docker build -f mammoth-mcp-server/deploy/Dockerfile -t mammoth-mcp-server .
#
# Run it with the settings `.env.example` lists:
#
#   docker run --env-file .env -p 8270:8270 mammoth-mcp-server
#
# The server keeps nothing in memory between requests, so it scales by adding
# containers. They share only Redis.

FROM python:3.13-slim AS build

WORKDIR /src
# Only what the two packages need to build, so an unrelated change does not
# rebuild this layer.
COPY pyproject.toml README.md LICENSE ./
COPY mammoth ./mammoth
COPY mammoth-mcp-server ./mammoth-mcp-server

# A virtual environment of its own, copied whole into the final image. Nothing
# that builds it reaches the image that runs.
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir . ./mammoth-mcp-server

FROM python:3.13-slim

# Runs as nobody's owner: the server writes no files and needs no root.
RUN useradd --create-home --uid 10001 mcp
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_PORT=8270

USER mcp
EXPOSE 8270

# The one route that answers without a token, so a probe needs no credentials.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request;urllib.request.urlopen(f\"http://127.0.0.1:{os.environ['MCP_PORT']}/.well-known/oauth-protected-resource/mcp\",timeout=4)"]

# One process per worker. Workers share only the Redis store.
#
# The address is fixed, and `MCP_HOST` is ignored on purpose: inside a container
# 127.0.0.1 is reachable by nothing, and `.env` carries that value for a server
# run on a host. What the port is exposed to is the publish rule's business,
# e.g. `-p 127.0.0.1:8270:8270`.
# The settings are checked first, and a bad one stops the container with its
# reason: a worker that dies at startup would otherwise be restarted for ever,
# and the container would look alive while serving nothing.
CMD ["sh", "-c", "python -c 'from mammoth_mcp_server.app import check_settings; check_settings()' && exec uvicorn mammoth_mcp_server.app:create_app --factory --host 0.0.0.0 --port \"$MCP_PORT\" --workers 2"]
