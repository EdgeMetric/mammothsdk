"""Environment variable configuration for Mammoth MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class MammothConfig:
    """Configuration loaded from environment variables."""

    api_key: str = ""
    api_secret: str = ""
    workspace_id: int = 0
    base_url: str = "https://app.mammoth.io/api/v2"
    project_id: int | None = None
    job_timeout: int = 120
    pipeline_timeout: int = 3600

    @classmethod
    def from_env(cls) -> MammothConfig:
        """Load configuration from environment variables.

        Required:
            MAMMOTH_API_KEY, MAMMOTH_API_SECRET, MAMMOTH_WORKSPACE_ID

        Optional:
            MAMMOTH_BASE_URL, MAMMOTH_PROJECT_ID, MAMMOTH_JOB_TIMEOUT,
            MAMMOTH_PIPELINE_TIMEOUT
        """
        api_key = os.environ.get("MAMMOTH_API_KEY", "")
        api_secret = os.environ.get("MAMMOTH_API_SECRET", "")
        workspace_id_str = os.environ.get("MAMMOTH_WORKSPACE_ID", "0")

        if not api_key or not api_secret or workspace_id_str == "0":
            raise ValueError(
                "Missing required environment variables: "
                "MAMMOTH_API_KEY, MAMMOTH_API_SECRET, MAMMOTH_WORKSPACE_ID"
            )

        project_id_str = os.environ.get("MAMMOTH_PROJECT_ID")
        project_id = int(project_id_str) if project_id_str else None

        return cls(
            api_key=api_key,
            api_secret=api_secret,
            workspace_id=int(workspace_id_str),
            base_url=os.environ.get("MAMMOTH_BASE_URL", cls.base_url),
            project_id=project_id,
            job_timeout=int(os.environ.get("MAMMOTH_JOB_TIMEOUT", str(cls.job_timeout))),
            pipeline_timeout=int(os.environ.get("MAMMOTH_PIPELINE_TIMEOUT", str(cls.pipeline_timeout))),
        )

    def summary(self) -> dict:
        """Return a safe summary (no secrets)."""
        return {
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "base_url": self.base_url,
            "job_timeout": self.job_timeout,
            "pipeline_timeout": self.pipeline_timeout,
            "api_key_set": bool(self.api_key),
            "api_secret_set": bool(self.api_secret),
        }
