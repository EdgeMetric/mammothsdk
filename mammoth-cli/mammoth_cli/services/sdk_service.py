"""SDK-backed implementation of :class:`~mammoth_cli.services.protocol.MammothService`.

Wraps exactly one :class:`mammoth.client.MammothClient` built from a resolved
authentication context. All Mammoth network access goes through this public
SDK client; this module never imports a transport library and never touches
a private (``_``-prefixed) SDK member.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

from mammoth.client import MammothClient

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.services.mapping import map_sdk_exception


class SdkMammothService:
    """Production :class:`~mammoth_cli.services.protocol.MammothService`."""

    def __init__(self, auth: ResolvedAuth, *, timeout: float | None = None) -> None:
        """Build the service from resolved authentication.

        Args:
            auth: Resolved API key, secret, workspace id, and base url.
            timeout: Optional per-request timeout override, in seconds.
        """
        kwargs: dict[str, Any] = {}
        if timeout is not None:
            kwargs["timeout"] = int(timeout)
        self._client = MammothClient(
            api_key=auth.api_key,
            api_secret=auth.api_secret,
            workspace_id=auth.workspace_id,
            base_url=auth.base_url,
            **kwargs,
        )

    def check_connection(self) -> dict[str, Any]:
        """Perform a lightweight authenticated call to verify credentials.

        Returns:
            The raw project-list response used as the connection probe.

        Raises:
            CliError: Mapped from any SDK exception (auth, network, timeout).
        """
        try:
            return self._client.projects.list(limit=1)
        except Exception as exc:
            raise map_sdk_exception(exc) from exc

    def list_projects(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        """List projects in the current workspace.

        The public SDK does not expose server-side pagination offsets, so an
        offset is applied client-side to the returned page.

        Args:
            limit: Maximum number of results.
            offset: Number of leading results to skip.

        Returns:
            The raw project-list response, sliced by ``offset``/``limit``.

        Raises:
            CliError: Mapped from any SDK exception.
        """
        try:
            response = self._client.projects.list(limit=limit + offset)
        except Exception as exc:
            raise map_sdk_exception(exc) from exc
        projects = response.get("projects", [])
        return {**response, "projects": projects[offset : offset + limit]}

    def get_project(self, project_id: int) -> dict[str, Any]:
        """Get one project by id.

        Args:
            project_id: The project id.

        Returns:
            The raw project response.

        Raises:
            CliError: Mapped from any SDK exception, including not-found.
        """
        try:
            return self._client.projects.get(project=project_id)
        except Exception as exc:
            raise map_sdk_exception(exc) from exc

    def create_project(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Create a project.

        Args:
            name: The project name.
            **kwargs: Additional creation options forwarded to the SDK.

        Returns:
            The raw created-project response.

        Raises:
            CliError: Mapped from any SDK exception.
        """
        try:
            return self._client.projects.create(name, **kwargs)
        except Exception as exc:
            raise map_sdk_exception(exc) from exc

    def delete_project(self, project_id: int) -> dict[str, Any]:
        """Delete a project.

        Args:
            project_id: The project id.

        Returns:
            The raw deletion response.

        Raises:
            CliError: Mapped from any SDK exception.
        """
        try:
            return self._client.projects.delete(project_id)
        except Exception as exc:
            raise map_sdk_exception(exc) from exc

    def close(self) -> None:
        """Close the owned HTTP session. Safe to call more than once."""
        self._client.close()

    def __enter__(self) -> SdkMammothService:
        """Enter the service as a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the service on context-manager exit."""
        self.close()
