"""Mammoth Analytics MCP Server — entry point and lifespan."""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from mammoth_mcp.config import MammothConfig
from mammoth_mcp.instructions import MAMMOTH_INSTRUCTIONS
from mammoth_mcp.settings import Settings
from mammoth_mcp.state import ClientManager

logger = logging.getLogger(__name__)

settings = Settings()


# ── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Create resources based on mode and expose them to all tools."""
    if settings.mode == "remote":
        # _shared_token_store and _shared_registry are created once in
        # _build_server().  We verify Redis connectivity here on first session.
        assert _shared_token_store is not None
        assert _shared_registry is not None
        await _shared_token_store.connect()
        logger.info("Mammoth MCP server starting (remote mode)")
        try:
            yield {"registry": _shared_registry}
        finally:
            pass  # Redis stays open across sessions
    else:
        config = MammothConfig.from_env()
        logger.info(
            "Mammoth MCP server starting (stdio) — workspace=%s, project=%s",
            config.workspace_id,
            config.project_id,
        )
        manager = ClientManager(config)
        yield {"manager": manager}


# ── Server construction ──────────────────────────────────────

_shared_token_store = None  # set in _build_server() for remote mode
_shared_registry = None  # set in _build_server() for remote mode


def _build_server() -> FastMCP:
    """Build the FastMCP server with appropriate auth settings for the mode."""
    global _shared_token_store, _shared_registry

    if settings.mode == "remote":
        from mammoth_mcp.oauth_provider import MammothOAuthProvider, register_login_routes
        from mammoth_mcp.state import UserClientRegistry
        from mammoth_mcp.token_store import RedisTokenStore
        from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
        from mcp.server.transport_security import TransportSecuritySettings

        # Single token store instance shared between OAuth provider and lifespan.
        # Created here (unconnected), connected in lifespan().
        _shared_token_store = RedisTokenStore(
            redis_url=settings.redis_url,
            auth_code_ttl=settings.auth_code_ttl,
            access_token_ttl=settings.access_token_ttl,
        )
        _shared_registry = UserClientRegistry(_shared_token_store, job_timeout=settings.mammoth_job_timeout)
        provider = MammothOAuthProvider(settings, _shared_token_store)

        auth_settings = AuthSettings(
            issuer_url=settings.server_url,
            resource_server_url=settings.server_url,
            client_registration_options=ClientRegistrationOptions(enabled=True),
            revocation_options=RevocationOptions(enabled=True),
        )

        # Allow the public hostname through DNS rebinding protection
        from urllib.parse import urlparse
        public_host = urlparse(settings.server_url).hostname or "localhost"
        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[public_host, f"{public_host}:*"],
        )

        server = FastMCP(
            "Mammoth Analytics",
            instructions=MAMMOTH_INSTRUCTIONS,
            lifespan=lifespan,
            auth_server_provider=provider,
            auth=auth_settings,
            transport_security=transport_security,
        )

        # Register custom login routes
        register_login_routes(server, settings, _shared_token_store)
        return server
    else:
        return FastMCP("Mammoth Analytics", instructions=MAMMOTH_INSTRUCTIONS, lifespan=lifespan)


mcp = _build_server()


# ── Resources ────────────────────────────────────────────────

@mcp.resource("mammoth://config")
def get_config() -> str:
    """Current Mammoth connection configuration (no secrets)."""
    import os

    config = {
        "workspace_id": os.environ.get("MAMMOTH_WORKSPACE_ID", ""),
        "project_id": os.environ.get("MAMMOTH_PROJECT_ID", ""),
        "base_url": os.environ.get("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
        "job_timeout": os.environ.get("MAMMOTH_JOB_TIMEOUT", "120"),
        "api_key_set": bool(os.environ.get("MAMMOTH_API_KEY")),
        "api_secret_set": bool(os.environ.get("MAMMOTH_API_SECRET")),
    }
    return json.dumps(config, indent=2)


@mcp.resource("mammoth://enums")
def get_enums() -> str:
    """All valid enum values for Mammoth SDK operations."""
    from mammoth import (
        AggregateFunction,
        ColumnType,
        DateComponent,
        DateDiffUnit,
        FillDirection,
        FilterType,
        JoinType,
        JsonType,
        MathOperator,
        Operator,
        SortDirection,
        SubstringDirection,
        TextCase,
        WindowFunction,
        WindowRange,
    )

    enums = {
        "Operator": [e.value for e in Operator],
        "ColumnType": [e.value for e in ColumnType],
        "JoinType": [e.value for e in JoinType],
        "TextCase": [e.value for e in TextCase],
        "DateComponent": [e.value for e in DateComponent],
        "DateDiffUnit": [e.value for e in DateDiffUnit],
        "WindowFunction": [e.value for e in WindowFunction],
        "WindowRange": [e.value for e in WindowRange],
        "FillDirection": [e.value for e in FillDirection],
        "AggregateFunction": [e.value for e in AggregateFunction],
        "FilterType": [e.value for e in FilterType],
        "SortDirection": [e.value for e in SortDirection],
        "MathOperator": [e.value for e in MathOperator],
        "SubstringDirection": [e.value for e in SubstringDirection],
        "JsonType": [e.value for e in JsonType],
    }
    return json.dumps(enums, indent=2)


# ── Register tools from submodules ───────────────────────────

from mammoth_mcp.tools import (  # noqa: E402
    advanced,
    aggregate,
    ai,
    columns,
    connection,
    data,
    discovery,
    export,
    help,
    pipeline,
    values,
    views,
)


# ── Entry points ─────────────────────────────────────────────

def create_app():
    """ASGI app factory for uvicorn (remote mode)."""
    from starlette.middleware.cors import CORSMiddleware

    app = mcp.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id", "WWW-Authenticate"],
    )
    return app


def _configure_logging() -> None:
    """Set up logging to stderr and optionally to a file."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if settings.log_file:
        handlers.append(logging.FileHandler(settings.log_file))

    logging.basicConfig(level=level, handlers=handlers, format=fmt, datefmt=datefmt)


def main() -> None:
    """Run the MCP server."""
    _configure_logging()
    if settings.mode == "remote":
        import uvicorn

        logger.info("Starting remote MCP server on %s:%s", settings.host, settings.port)
        uvicorn.run(
            "mammoth_mcp.server:create_app",
            factory=True,
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level.lower(),
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
