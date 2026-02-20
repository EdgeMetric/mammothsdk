"""Pydantic settings — all server configuration from .env / environment."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    server_url: str = "https://mcp.mammoth.io"
    mode: str = "stdio"  # "stdio" or "remote"
    log_level: str = "INFO"
    log_file: str = ""  # Path to log file (empty = stderr only)

    # Redis (remote mode only)
    redis_url: str = "redis://localhost:6379/0"
    auth_code_ttl: int = 300  # 5 min
    access_token_ttl: int = 2592000  # 30 days

    # Mammoth defaults
    mammoth_base_url: str = "https://app.mammoth.io/api/v2"
    mammoth_job_timeout: int = 120
    mammoth_pipeline_timeout: int = 3600

    # Stdio mode only (ignored in remote mode)
    mammoth_api_key: str = ""
    mammoth_api_secret: str = ""
    mammoth_workspace_id: int = 0
    mammoth_project_id: int | None = None
