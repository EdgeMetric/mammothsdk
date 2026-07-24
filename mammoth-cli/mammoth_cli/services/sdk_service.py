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
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENTS,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.output.progress import spinner
from mammoth_cli.services.coerce import coerce_arguments
from mammoth_cli.services.conditions import CONDITION_KWARG, compile_condition
from mammoth_cli.services.dispatch import resolve_sdk_method
from mammoth_cli.services.mapping import map_sdk_exception


class SdkMammothService:
    """Production :class:`~mammoth_cli.services.protocol.MammothService`."""

    def __init__(
        self,
        auth: ResolvedAuth,
        *,
        timeout: float | None = None,
        job_timeout: float | None = None,
        pipeline_timeout: float | None = None,
        project_id: int | None = None,
        progress: bool = False,
    ) -> None:
        """Build the service from resolved authentication.

        Args:
            auth: Resolved API key, secret, workspace id, and base url.
            timeout: Optional per-request timeout override, in seconds.
            job_timeout: Optional job-wait timeout override, in seconds; bound
                on the client so async job waits honor it.
            pipeline_timeout: Optional pipeline-readiness timeout override, in
                seconds; bound on the client so pipeline waits honor it.
            project_id: Active project id to bind on the client, so SDK methods
                that read the client's project context (rather than taking an
                explicit ``project_id`` argument) resolve to it.
            progress: Whether to show a stderr spinner while a call is in
                flight. Set from the resolved output policy; false for machine
                output, ``--no-progress``, non-terminals, and CI.
        """
        self._progress = progress
        kwargs: dict[str, Any] = {}
        if timeout is not None:
            kwargs["timeout"] = int(timeout)
        if job_timeout is not None:
            kwargs["job_timeout"] = int(job_timeout)
        if pipeline_timeout is not None:
            kwargs["pipeline_timeout"] = int(pipeline_timeout)
        self._client = MammothClient(
            api_key=auth.api_key,
            api_secret=auth.api_secret,
            workspace_id=auth.workspace_id,
            base_url=auth.base_url,
            **kwargs,
        )
        if project_id is not None:
            self._client.set_project_id(project_id)

    def call(self, sdk_symbol: str, /, **kwargs: Any) -> Any:
        """Resolve and invoke the public SDK method named by ``sdk_symbol``.

        Args:
            sdk_symbol: The dotted symbol naming the backing public SDK method.
            **kwargs: Keyword arguments forwarded to the method.

        Returns:
            The raw SDK return value.

        Raises:
            CliError: ``sdk_symbol_unresolved`` when no public method matches;
                ``invalid_arguments`` when the supplied fields do not fit the
                method signature; otherwise the mapped SDK exception.
        """
        method = resolve_sdk_method(self._client, sdk_symbol)
        kwargs = self._coerce_call_arguments(method, kwargs)
        try:
            with spinner(self._progress):
                return method(**kwargs)
        except TypeError as exc:
            raise CliError(
                code=CODE_INVALID_ARGUMENTS,
                message=f"The supplied fields do not fit '{sdk_symbol}'.",
                exit_status=EXIT_USAGE,
                hint="Check the command schema with 'mammoth schema get'.",
                details={"reason": str(exc)},
            ) from exc
        except Exception as exc:
            raise map_sdk_exception(exc) from exc

    @staticmethod
    def _coerce_call_arguments(method: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Coerce generic-``call`` kwargs to the method's annotated types.

        The rich ``View`` path coerces JSON-shaped input into the dataclasses,
        enums, and pydantic models the SDK expects; the generic ``call`` path
        used by every non-View command must do the same, or a command whose SDK
        method takes a pydantic model (``automation create``, ``client-app
        update``, ``external-key create``) crashes on the raw dict.

        Coercion is best-effort: a method whose annotations cannot be resolved
        (for example an API module that imports its types only under
        ``TYPE_CHECKING`` and names one this module's namespace does not carry)
        falls back to the raw kwargs, so currently-working commands are never
        broken by a resolution failure. A genuinely bad value still surfaces as
        the SDK's own ``TypeError``/validation error at call time.

        Args:
            method: The resolved bound SDK method about to be invoked.
            kwargs: The raw JSON-shaped keyword arguments.

        Returns:
            The coerced kwargs, or the original kwargs if coercion is not
            possible for this method.
        """
        try:
            return coerce_arguments(method, kwargs)
        except Exception:
            return kwargs

    def wait_if_job(self, response: Any) -> Any:
        """Wait for a recognized job response using the client's configured timeout."""
        try:
            with spinner(self._progress):
                return self._client.wait_if_job(response)
        except Exception as exc:
            raise map_sdk_exception(exc) from exc

    def call_view(self, view_id: int, method: str, /, **kwargs: Any) -> Any:
        """Resolve a View and invoke one of its public methods (or a property).

        Args:
            view_id: The dataview id to resolve into a View.
            method: The public View method or property name.
            **kwargs: Keyword arguments forwarded to the method; a ``condition``
                spec is compiled to an SDK condition object first.

        Returns:
            The raw return value, or the property value for a non-callable
            attribute such as ``is_draft_mode``.

        Raises:
            CliError: ``sdk_symbol_unresolved`` when the View has no such public
                member; ``invalid_arguments`` when the fields do not fit the
                method; ``invalid_condition`` for a bad condition spec;
                otherwise the mapped SDK exception.
        """
        try:
            with spinner(self._progress):
                view = self._client.get_view(view_id)
        except Exception as exc:
            raise map_sdk_exception(exc) from exc
        if method.startswith("_"):
            raise self._view_member_error(view_id, method)
        attribute = getattr(view, method, None)
        if attribute is None:
            raise self._view_member_error(view_id, method)
        if not callable(attribute):
            return attribute
        try:
            kwargs = coerce_arguments(attribute, kwargs)
        except (ValueError, TypeError) as exc:
            raise CliError(
                code=CODE_INVALID_ARGUMENTS,
                message=f"The supplied fields do not fit View.{method}.",
                exit_status=EXIT_USAGE,
                hint="Check the command schema with 'mammoth schema get'.",
                details={"reason": str(exc)},
            ) from exc
        if kwargs.get(CONDITION_KWARG) is not None:
            kwargs[CONDITION_KWARG] = compile_condition(kwargs[CONDITION_KWARG])
        try:
            with spinner(self._progress):
                return attribute(**kwargs)
        except TypeError as exc:
            raise CliError(
                code=CODE_INVALID_ARGUMENTS,
                message=f"The supplied fields do not fit View.{method}.",
                exit_status=EXIT_USAGE,
                hint="Check the command schema with 'mammoth schema get'.",
                details={"reason": str(exc)},
            ) from exc
        except Exception as exc:
            raise map_sdk_exception(exc) from exc

    @staticmethod
    def _view_member_error(view_id: int, method: str) -> CliError:
        return CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"View {view_id} has no public method '{method}'.",
            exit_status=EXIT_USAGE,
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
