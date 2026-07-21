"""Typed protocol for the Mammoth service boundary used by CLI commands.

Every bespoke command depends on this protocol, never on
:class:`mammoth.client.MammothClient` directly, so command tests can supply a
typed fake with no network access. The surface is intentionally minimal; it
grows as later command families are implemented.
"""

from __future__ import annotations

from typing import Any, Protocol


class MammothService(Protocol):
    """The typed operations the auth/project command families need."""

    def call(self, sdk_symbol: str, /, **kwargs: Any) -> Any:
        """Invoke the public SDK method named by ``sdk_symbol``.

        This is the generic seam every manifest-driven command uses: the
        command supplies the reviewed ``sdk_symbol`` and validated keyword
        arguments, and the service resolves and calls the matching public
        method, mapping any SDK exception to a stable
        :class:`~mammoth_cli.errors.envelope.CliError`.

        Args:
            sdk_symbol: The dotted symbol naming the backing public SDK method.
            **kwargs: Keyword arguments forwarded to the method.

        Returns:
            The raw SDK return value (typically a mapping).
        """
        ...

    def check_connection(self) -> dict[str, Any]:
        """Perform a lightweight authenticated call and return its raw result.

        Returns:
            The raw response used as the connection probe.
        """
        ...

    def list_projects(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        """List projects in the current workspace.

        Args:
            limit: Maximum number of results.
            offset: Number of leading results to skip.

        Returns:
            The raw project-list response.
        """
        ...

    def get_project(self, project_id: int) -> dict[str, Any]:
        """Get one project by id.

        Args:
            project_id: The project id.

        Returns:
            The raw project response.
        """
        ...

    def create_project(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Create a project.

        Args:
            name: The project name.
            **kwargs: Additional creation options.

        Returns:
            The raw created-project response.
        """
        ...

    def delete_project(self, project_id: int) -> dict[str, Any]:
        """Delete a project.

        Args:
            project_id: The project id.

        Returns:
            The raw deletion response.
        """
        ...

    def close(self) -> None:
        """Release any held resources (for example, the HTTP session)."""
        ...

    def __enter__(self) -> MammothService:
        """Enter the service as a context manager."""
        ...

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close the service on context-manager exit."""
        ...
