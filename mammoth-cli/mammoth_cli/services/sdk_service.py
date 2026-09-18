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
from mammoth.exceptions import MammothColumnError

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENTS,
    CODE_MISSING_ARGUMENT,
    CODE_RESOURCE_NOT_FOUND,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_NOT_FOUND,
    EXIT_USAGE,
    CliError,
    missing_project_error,
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
        profile: str | None = None,
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
            profile: Resolved, non-secret credential profile used to render
                recovery commands without falling back to mutable defaults.
            progress: Whether to show a stderr spinner while a call is in
                flight. Set from the resolved output policy; false for machine
                output, ``--no-progress``, non-terminals, and CI.
        """
        self._progress = progress
        self._profile = profile
        self._project_id = project_id
        self._workspace_id = auth.workspace_id
        kwargs: dict[str, Any] = {}
        if timeout is not None:
            # Preserve fractional per-request timeouts; truncating 0.5 to 0
            # disables the intended request budget in requests/urllib3.
            kwargs["timeout"] = timeout
        if job_timeout is not None:
            kwargs["job_timeout"] = job_timeout
        if pipeline_timeout is not None:
            kwargs["pipeline_timeout"] = pipeline_timeout
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
        # These public seams ultimately build project-scoped URLs and otherwise
        # raise a raw SDK ValueError when ``--project`` was omitted.  Validate
        # the CLI precondition here so release commands fail as stable usage
        # errors before any transport call (or generic ``api_error`` envelope).
        if (
            sdk_symbol
            in {
                "mammoth.api.pipeline.PipelineAPI.items_all",
                "mammoth.client.ViewsResource.delete",
                "mammoth.client.ViewsResource.get",
            }
            and self._client.project_id is None
        ):
            raise missing_project_error()
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
            raise map_sdk_exception(
                exc,
                profile=self._profile,
                project_id=self._project_id,
                workspace_id=self._workspace_id,
            ) from exc

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

    def wait_if_job(self, response: Any, *, dashboard_url: str | None = None) -> Any:
        """Wait for a recognized job response using the client's configured timeout.

        ``dashboard_url`` names a published dashboard's URL slug: jobs those
        routes dispatch are readable only through the URL-scoped job route
        (``GET /jobs/{id}`` answers ``4PERM002`` and used to fail the command
        although the job succeeded), so the wait observes ``job_by_url``.
        """
        try:
            with spinner(self._progress):
                if dashboard_url is None:
                    return self._client.wait_if_job(response)
                dashboards = self._client.dashboards
                return self._client.wait_if_job(
                    response,
                    fetch=lambda job_id, _remaining: dashboards.job_by_url(dashboard_url, job_id),
                )
        except Exception as exc:
            raise map_sdk_exception(exc) from exc

    def call_view(
        self,
        view_id: int,
        method: str,
        /,
        dataset_id: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Resolve a View and invoke one of its public methods (or a property).

        Args:
            view_id: The dataview id to resolve into a View.
            method: The public View method or property name.
            dataset_id: Optional verified parent dataset for the target view.
                When supplied, metadata is fetched from that exact parent
                endpoint rather than using a workspace-wide parent search.
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
        if self._client.project_id is None:
            raise missing_project_error()
        try:
            with spinner(self._progress):
                # A supplied parent is part of the resource identity. Calling
                # get_view would discard it and re-enter the legacy resolver,
                # potentially probing an unrelated parent and returning a
                # misleading 403.
                view = (
                    self._client.get_view(view_id)
                    if dataset_id is None
                    else self._client.views.get(view_id, dataset_id=dataset_id)
                )
        except ValueError as exc:
            # The SDK's project-wide parent discovery reports a miss as a bare
            # ValueError. Name it, and hand back the reads that settle it,
            # instead of flattening it into "operation failed unexpectedly".
            if "not found in any dataset" not in str(exc):
                raise map_sdk_exception(exc) from exc
            project = self._client.project_id
            raise CliError(
                code=CODE_RESOURCE_NOT_FOUND,
                message=(
                    f"View {view_id} was not found in any dataset of project {project}; "
                    "parent discovery walked every visible dataset and folder."
                ),
                exit_status=EXIT_NOT_FOUND,
                hint=(
                    "Check the project (views live in exactly one project) and pass the "
                    "exact parent DATASET_ID from 'view list DATASET_ID' or a dataset "
                    "read; do not rely on discovery for large projects."
                ),
                details={"view_id": view_id, "project_id": project, "reason": str(exc)},
                recovery_commands=[
                    f"mammoth dataset list --project {project} --output json --no-input",
                    "mammoth dataset find NAME_SUBSTRING --output json --no-input",
                ],
            ) from exc
        except Exception as exc:
            raise map_sdk_exception(exc) from exc
        if method.startswith("_"):
            raise self._view_member_error(view_id, method)
        attribute = getattr(view, method, None)
        # Typed export conveniences live on ``view.export`` rather than on
        # ``View`` itself.  Keep the public call seam single and scoped while
        # allowing reviewed command handlers to invoke those helpers without
        # reaching into private SDK state.
        if attribute is None and not method.startswith("_"):
            export = getattr(view, "export", None)
            attribute = getattr(export, method, None)
        if attribute is None:
            raise self._view_member_error(view_id, method)
        if not callable(attribute):
            return attribute
        # Join/lookup resolve foreign display names against the foreign view's
        # own metadata. Hydrate integer references into rich Views before the
        # SDK builders run, using the exact foreign parent when supplied.
        try:
            if method == "join":
                kwargs = self._hydrate_foreign_view(
                    kwargs, view_kwarg="foreign_view", parent_kwarg="foreign_dataset_id"
                )
            elif method == "lookup":
                kwargs = self._hydrate_foreign_view(
                    kwargs, view_kwarg="lookup_view_id", parent_kwarg="lookup_dataset_id"
                )
        except CliError:
            raise
        except Exception as exc:
            raise map_sdk_exception(exc) from exc
        self._reject_internal_column_inputs(view, method, kwargs)
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
        except MammothColumnError as exc:
            # Column validation happens while building the task, before the
            # SDK can POST. Preserve a useful agent-facing error envelope
            # rather than flattening it into a generic API error.
            available = sorted(getattr(view, "columns", {}) or {})
            raise self.column_input_error(str(exc), available) from exc
        except ValueError as exc:
            if method == "math" and "Unrecognized token" in str(exc):
                available = sorted(getattr(view, "columns", {}) or {})
                raise self.column_input_error("expression", available) from exc
            raise CliError(
                code=CODE_INVALID_ARGUMENTS,
                message=f"The supplied fields do not fit View.{method}.",
                exit_status=EXIT_USAGE,
                hint="Check the command schema with 'mammoth schema get'.",
                details={"reason": str(exc)},
            ) from exc
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

    def _hydrate_foreign_view(
        self,
        kwargs: dict[str, Any],
        *,
        view_kwarg: str,
        parent_kwarg: str,
    ) -> dict[str, Any]:
        """Resolve an integer foreign view reference to a scoped rich View.

        Integer references historically skipped foreign metadata, forcing
        internal column ids and allowing an unscoped lookup. CLI column inputs
        are display names, so metadata must be fetched before the mutation.
        """
        value = kwargs.get(view_kwarg)
        # Also accept a structured reference when callers compose service calls
        # directly; the ordinary CLI shape remains id + *_dataset_id.
        if isinstance(value, dict):
            raw_view_id = value.get("view_id", value.get("dataview_id", value.get("id")))
            if raw_view_id is None:
                return kwargs
            kwargs = dict(kwargs)
            kwargs[view_kwarg] = int(raw_view_id)
            if kwargs.get(parent_kwarg) is None and value.get("dataset_id") is not None:
                kwargs[parent_kwarg] = int(value["dataset_id"])
            value = kwargs[view_kwarg]
        if not isinstance(value, int) or isinstance(value, bool):
            return kwargs
        parent = kwargs.get(parent_kwarg)
        if parent is None:
            # Resolving the foreign view without its parent would re-enter the
            # SDK's project-wide browse-and-probe discovery before a mutation,
            # the same path the target view is already protected from.
            raise CliError(
                code=CODE_MISSING_ARGUMENT,
                message=(
                    f"'{view_kwarg}' {value} needs its exact parent '{parent_kwarg}'; "
                    "project-wide parent discovery is only performed for reads."
                ),
                exit_status=EXIT_USAGE,
                hint=(
                    f"Add '{parent_kwarg}' to --input with the dataset that owns view {value} "
                    "(from 'view list DATASET_ID' or a 'view get' read)."
                ),
                details={view_kwarg: value, "missing_field": parent_kwarg},
                recovery_commands=[f"mammoth view get {value} --output json --no-input"],
            )
        foreign = self._client.views.get(value, dataset_id=int(parent))
        hydrated = dict(kwargs)
        hydrated[view_kwarg] = foreign
        return hydrated

    @staticmethod
    def _reject_internal_column_inputs(view: Any, method: str, kwargs: dict[str, Any]) -> None:
        """Reject backend column ids at the CLI boundary.

        The SDK intentionally remains backwards-compatible with internal
        names.  Agent-facing CLI inputs are stricter: all source references
        must be display names, while output aliases remain ordinary strings.
        This check runs after metadata hydration and before any task POST.
        """
        local_columns = getattr(view, "columns", {}) or {}
        local_internal = {value for value in local_columns.values() if isinstance(value, str)}
        local_display = set(local_columns)

        def check(value: Any, *, scope: str, columns: dict[str, str], display: set[str]) -> None:
            internal = {item for item in columns.values() if isinstance(item, str)}
            if isinstance(value, str):
                # Exact standalone names only; do not rewrite or mutate
                # expressions, and do not flag a display name that happens to
                # equal an internal name.
                if value in internal and value not in display:
                    raise SdkMammothService.column_input_error(
                        value, sorted(display), internal=True, scope=scope
                    )
                if value not in display and value not in internal:
                    raise SdkMammothService.column_input_error(value, sorted(display), scope=scope)
                return
            if isinstance(value, list):
                for index, item in enumerate(value):
                    check(item, scope=f"{scope}[{index}]", columns=columns, display=display)

        # Plain local references shared by the transform mixins.
        for name in (
            "column",
            "source",
            "start",
            "end",
            "existing_column",
            "columns",
            "sources",
            "group_by",
            "partition_by",
        ):
            if name in kwargs:
                check(kwargs[name], scope=name, columns=local_columns, display=local_display)

        # Internal-dataset exports use a source -> destination mapping. Only
        # the source keys identify existing view columns; destination names are
        # user-authored output labels and must remain untouched.
        column_mapping = kwargs.get("column_mapping")
        if isinstance(column_mapping, dict):
            for source_name in column_mapping:
                check(
                    source_name,
                    scope="column_mapping",
                    columns=local_columns,
                    display=local_display,
                )

        expression = kwargs.get("expression")
        if isinstance(expression, str):
            # Match the same longest-name/boundary convention as the SDK's
            # expression parser. This handles spaces, quotes and Unicode
            # display names without substring replacement or false positives
            # where an internal id is merely part of a longer display name.
            names = sorted(local_display | local_internal, key=len, reverse=True)
            pos = 0
            while pos < len(expression):
                matched = next(
                    (
                        name
                        for name in names
                        if expression.startswith(name, pos)
                        and (
                            pos + len(name) == len(expression)
                            or not (
                                expression[pos + len(name)].isalnum()
                                or expression[pos + len(name)] == "_"
                            )
                        )
                    ),
                    None,
                )
                if matched is not None:
                    if matched in local_internal and matched not in local_display:
                        raise SdkMammothService.column_input_error(
                            matched,
                            sorted(local_display),
                            internal=True,
                            scope="expression",
                        )
                    pos += len(matched)
                else:
                    pos += 1

        condition = kwargs.get(CONDITION_KWARG)

        def check_condition(spec: Any) -> None:
            if not isinstance(spec, dict):
                return
            if "column" in spec:
                check(
                    spec["column"],
                    scope="condition.column",
                    columns=local_columns,
                    display=local_display,
                )
            if spec.get("value_is_column") and "value" in spec:
                check(
                    spec["value"],
                    scope="condition.value",
                    columns=local_columns,
                    display=local_display,
                )
            for key in ("and", "or"):
                branches = spec.get(key)
                if isinstance(branches, list):
                    for branch in branches:
                        check_condition(branch)
            if "not" in spec:
                check_condition(spec["not"])

        check_condition(condition)

        if method == "join":
            foreign = kwargs.get("foreign_view")
            foreign_columns = getattr(foreign, "columns", {}) or {}
            foreign_display = set(foreign_columns)
            for key in kwargs.get("on", []) or []:
                if isinstance(key, dict) and "left" in key:
                    check(
                        key["left"],
                        scope="on.left",
                        columns=local_columns,
                        display=local_display,
                    )
                if isinstance(key, dict) and "right" in key:
                    check(
                        key["right"],
                        scope="on.right",
                        columns=foreign_columns,
                        display=foreign_display,
                    )
            for item in kwargs.get("select", []) or []:
                value = item.get("column") if isinstance(item, dict) else item
                check(value, scope="select", columns=foreign_columns, display=foreign_display)
        elif method == "lookup":
            foreign = kwargs.get("lookup_view_id")
            foreign_columns = getattr(foreign, "columns", {}) or {}
            foreign_display = set(foreign_columns)
            check(
                kwargs.get("key"),
                scope="key",
                columns=foreign_columns,
                display=foreign_display,
            )
            check(
                kwargs.get("value"),
                scope="value",
                columns=foreign_columns,
                display=foreign_display,
            )

    @staticmethod
    def column_input_error(
        reference: str,
        available: list[str],
        *,
        internal: bool = False,
        scope: str | None = None,
    ) -> CliError:
        """Build a stable pre-mutation display-name resolution error."""
        if internal:
            message = f"{reference} must use a display name, not an internal column id."
            code = "internal_column_name"
        else:
            message = f"Column reference '{reference}' is not a display name in this view."
            code = "unknown_column"
        return CliError(
            code=code,
            message=message,
            exit_status=EXIT_USAGE,
            hint="Use one of the available display names from view metadata.",
            details={"reference": reference, "scope": scope, "available": available},
        )

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
