"""Mammoth Analytics MCP Server — entry point and lifespan."""

from __future__ import annotations

import importlib
import json
import logging
import logging.config
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from mammoth_mcp.config import MammothConfig
from mammoth_mcp.instructions import UNIFIED_INSTRUCTIONS
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
            logger.info("MCP session ended")
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

    instructions = UNIFIED_INSTRUCTIONS

    if settings.mode == "remote":
        from mcp.server.auth.settings import (
            AuthSettings,
            ClientRegistrationOptions,
            RevocationOptions,
        )
        from mcp.server.transport_security import TransportSecuritySettings

        from mammoth_mcp.oauth_provider import MammothOAuthProvider, register_login_routes
        from mammoth_mcp.state import UserClientRegistry
        from mammoth_mcp.token_store import RedisTokenStore

        # Single token store instance shared between OAuth provider and lifespan.
        # Created here (unconnected), connected in lifespan().
        _shared_token_store = RedisTokenStore(
            redis_url=settings.redis_url,
            auth_code_ttl=settings.auth_code_ttl,
            access_token_ttl=settings.access_token_ttl,
            encryption_key=settings.encryption_key,
        )
        _shared_registry = UserClientRegistry(
            _shared_token_store,
            job_timeout=settings.mammoth_job_timeout,
            pipeline_timeout=settings.mammoth_pipeline_timeout,
        )
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
            instructions=instructions,
            lifespan=lifespan,
            auth_server_provider=provider,
            auth=auth_settings,
            transport_security=transport_security,
        )

        # Register custom login routes
        register_login_routes(server, settings, _shared_token_store)
        return server
    else:
        return FastMCP("Mammoth Analytics", instructions=instructions, lifespan=lifespan)


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


# ── Tool registration (all tools loaded at startup) ──────────

_ALL_MODULES = [
    # Connection & discovery
    "connection", "discovery", "views", "data", "pipeline", "help",
    # Import & export
    "webhooks", "files_extended", "batches", "export",
    # Transformations
    "views_management", "columns", "values", "aggregate", "advanced", "ai",
    # Connectors
    "connectors",
    # Draft mode
    "draft_mode",
    # Admin & workspace
    "organization", "dashboards", "automations", "admin", "client_apps", "ai_extended",
]

for _module_name in _ALL_MODULES:
    importlib.import_module(f"mammoth_mcp.tools.{_module_name}")


# ── Entry points ─────────────────────────────────────────────


def create_app():
    """ASGI app factory for uvicorn (remote mode).

    Configures logging here so it works both when called from main()
    (log_config passed to uvicorn) and when run directly via
    ``uvicorn mammoth_mcp.server:create_app --factory``.
    """
    _configure_logging()

    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    from mammoth_mcp.rate_limit import RateLimitMiddleware

    app = mcp.streamable_http_app()

    # ── Health check endpoint ────────────────────────────────
    async def health_check(request: Request) -> JSONResponse:
        try:
            if _shared_token_store:
                await _shared_token_store._r.ping()
            return JSONResponse({"status": "healthy", "redis": "connected"})
        except Exception as e:
            return JSONResponse({"status": "unhealthy", "redis": str(e)}, status_code=503)

    app.routes.insert(0, Route("/health", health_check, methods=["GET"]))

    # ── Rate limiting ────────────────────────────────────────
    app.add_middleware(
        RateLimitMiddleware,
        redis_url=settings.redis_url,
        rpm=settings.rate_limit_rpm,
        burst=settings.rate_limit_burst,
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Mcp-Session-Id"],
        expose_headers=["Mcp-Session-Id", "WWW-Authenticate"],
    )
    return app


def _build_log_config() -> dict:
    """Build a logging dictConfig that uvicorn and stdlib both understand.

    Creates the log file's parent directory if it doesn't exist.
    """
    level = settings.log_level.upper()

    formatters: dict = {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    if settings.log_format == "json":
        formatters["default"] = {
            "()": f"{__name__}._JsonFormatter",
        }

    handlers: dict = {
        "stderr": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "formatter": "default",
        },
    }
    handler_names = ["stderr"]

    if settings.log_file:
        os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": settings.log_file,
            "formatter": "default",
        }
        handler_names.append("file")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "root": {"level": level, "handlers": handler_names},
        # Keep uvicorn's own loggers using the same config
        "loggers": {
            "uvicorn": {"level": level, "handlers": handler_names, "propagate": False},
            "uvicorn.error": {"level": level},
            "uvicorn.access": {"level": level},
        },
    }


class _JsonFormatter(logging.Formatter):
    """Structured JSON log formatter for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        import json as _json

        return _json.dumps(
            {
                "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
            }
        )


def _configure_logging() -> None:
    """Apply log config via dictConfig. Works for both main() and create_app()."""
    logging.config.dictConfig(_build_log_config())


def main() -> None:
    """Run the MCP server."""
    if settings.mode == "remote":
        import uvicorn

        log_config = _build_log_config()
        logger.info("Starting remote MCP server on %s:%s", settings.host, settings.port)
        uvicorn.run(
            "mammoth_mcp.server:create_app",
            factory=True,
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level.lower(),
            log_config=log_config,
            timeout_graceful_shutdown=30,
        )
    else:
        _configure_logging()
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
