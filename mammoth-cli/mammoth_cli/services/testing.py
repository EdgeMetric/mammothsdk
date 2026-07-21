"""A typed fake :class:`~mammoth_cli.services.protocol.MammothService`.

Used by command tests in place of the real SDK-backed service so no network
call is ever made. Kept in the package (not ``tests/``) so both unit and
contract tests can import one shared fake, mirroring
:mod:`mammoth_cli.testing`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mammoth_cli.errors.envelope import EXIT_AUTH, EXIT_NOT_FOUND, CliError


@dataclass
class FakeMammothService:
    """In-memory fake used by command tests instead of the real SDK service.

    Attributes:
        connection_ok: Whether :meth:`check_connection` succeeds.
        projects: The in-memory project records.
        calls: The ordered list of method names invoked, for assertions.
    """

    connection_ok: bool = True
    projects: list[dict[str, Any]] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    responses: dict[str, Any] = field(default_factory=dict)
    call_log: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def call(self, sdk_symbol: str, /, **kwargs: Any) -> Any:
        """Record the generic call and return a programmed response.

        Args:
            sdk_symbol: The symbol the handler dispatched to.
            **kwargs: The keyword arguments the handler passed; recorded in
                :attr:`call_log` so tests can assert exact field mapping.

        Returns:
            ``responses[sdk_symbol]`` if programmed (raised when it is an
            exception), else an empty mapping.
        """
        self.calls.append(sdk_symbol)
        self.call_log.append((sdk_symbol, dict(kwargs)))
        if sdk_symbol in self.responses:
            programmed = self.responses[sdk_symbol]
            if isinstance(programmed, Exception):
                raise programmed
            return programmed
        return {}

    def check_connection(self) -> dict[str, Any]:
        """Simulate a lightweight connection check."""
        self.calls.append("check_connection")
        if not self.connection_ok:
            raise CliError(
                code="authentication_failed",
                message="Mammoth rejected the provided credentials.",
                exit_status=EXIT_AUTH,
                recovery_commands=["mammoth auth login"],
            )
        return {"projects": self.projects[:1]}

    def list_projects(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        """Return the in-memory project list, sliced by offset/limit."""
        self.calls.append("list_projects")
        return {"projects": self.projects[offset : offset + limit]}

    def get_project(self, project_id: int) -> dict[str, Any]:
        """Return one in-memory project, or raise ``resource_not_found``."""
        self.calls.append("get_project")
        for project in self.projects:
            if project.get("id") == project_id:
                return project
        raise CliError(
            code="resource_not_found",
            message=f"Project {project_id} does not exist.",
            exit_status=EXIT_NOT_FOUND,
        )

    def create_project(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Create an in-memory project record."""
        self.calls.append("create_project")
        record = {"id": len(self.projects) + 1, "name": name}
        self.projects.append(record)
        return record

    def delete_project(self, project_id: int) -> dict[str, Any]:
        """Delete an in-memory project record."""
        self.calls.append("delete_project")
        self.projects = [p for p in self.projects if p.get("id") != project_id]
        return {"deleted": project_id}

    def close(self) -> None:
        """Record that the service was closed."""
        self.calls.append("close")

    def __enter__(self) -> FakeMammothService:
        """Enter the service as a context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close the service on context-manager exit."""
        self.close()
