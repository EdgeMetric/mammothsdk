"""Resolved command contracts used by the M2 binding pilot.

The command manifest describes policy and the public SDK signature describes
the callable fields.  This module joins those two existing sources into one
small, immutable description for the commands that have migrated to the
contract pilot.  It intentionally does not replace the manifest or the SDK
coercion layer: domain handlers still own transformations such as compiling a
condition and expanding upload positionals.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import Any, cast

from mammoth.models.batches import (
    ColumnIdMapping,
    ColumnNameMapping,
    NewDsDetails,
    ProjectedSourceColumn,
)

from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.services.argspec import ArgSpec, FieldSpec, arg_spec
from mammoth_cli.services.input_fields import (
    accepts_resource_dataset,
    excluded_input_fields,
    handler_owned_fields,
    is_closed_zero_input,
)
from mammoth_cli.services.openapi_types import openapi_body_schema_for
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals
from mammoth_cli.services.type_system import is_opaque_mapping, json_schema


class ContractBindingError(ValueError):
    """Raised when a supplied input has no declared contract destination."""


def _freeze(value: Any) -> Any:
    """Recursively freeze JSON-shaped metadata used by a contract."""
    if isinstance(value, dict):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def thaw_contract_metadata(value: Any) -> Any:
    """Return a JSON-library-compatible copy of frozen contract metadata."""
    if isinstance(value, Mapping):
        return {str(key): thaw_contract_metadata(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw_contract_metadata(item) for item in value]
    return value


def _record_policy(record: Mapping[str, Any], key: str, default: Any = None) -> Any:
    """Read a manifest policy value without allowing mutable record leakage."""
    value = record.get(key, default)
    return _freeze(value) if isinstance(value, (dict, list)) else value


@dataclass(frozen=True)
class ResolvedCommandContract:
    """The immutable binding and policy description for one command.

    ``fields`` contains only fields accepted from the input document.  A
    positional or authenticated context value is represented separately in
    ``context_bindings`` and therefore cannot be supplied by a JSON document.
    ``adapter_inputs`` documents fields whose value is deliberately consumed
    or transformed by a domain adapter before the SDK call.
    """

    command_id: str
    sdk_symbol: str | None
    fields: tuple[FieldSpec, ...]
    positionals: tuple[PositionalSpec, ...]
    input_bindings: Mapping[str, str]
    adapter_inputs: frozenset[str]
    context_bindings: Mapping[str, str]
    input_schema: Mapping[str, Any] | None
    extensibility: str
    mutation_class: str | None
    confirmation: str | None
    wait_policy: str | None
    result_model: str | None
    capability_identity: tuple[str, ...]

    @property
    def accepted_fields(self) -> tuple[FieldSpec, ...]:
        """The accepted input fields, in SDK signature order."""
        return self.fields

    @property
    def accepted_field_names(self) -> frozenset[str]:
        """Names admitted from a structured input document.

        This is deliberately exposed by the resolved contract instead of
        requiring callers to rebuild a set from SDK introspection. Admission,
        schema discovery and binding therefore share the same post-filtered
        field set (including positional/context exclusions).
        """
        return frozenset(field.name for field in self.fields)

    @property
    def declared_input_names(self) -> frozenset[str]:
        """Input names with an explicit binding or adapter consumption rule."""
        return self.accepted_field_names | self.adapter_inputs

    @property
    def accepts_extra(self) -> bool:
        """Whether the SDK callable declares a ``**kwargs`` extension point."""
        return self.extensibility != "closed"

    @property
    def sdk_keyword_bindings(self) -> Mapping[str, str]:
        """Explicit name used by callers that distinguish input from SDK bindings."""
        return self.input_bindings

    @property
    def effects(self) -> str | None:
        """Manifest effect/mutation classification."""
        return self.mutation_class

    @property
    def wait_behavior(self) -> str | None:
        """Manifest async wait policy."""
        return self.wait_policy

    @property
    def result_contract(self) -> str | None:
        """Public result model name associated with the command."""
        return self.result_model

    @property
    def capability_id(self) -> tuple[str, ...]:
        """Stable OpenAPI capability identity for the command."""
        return self.capability_identity

    def bind(self, document: Mapping[str, Any] | None = None, **context: Any) -> dict[str, Any]:
        """Bind input fields and explicit context to SDK keyword names.

        A positional/context value wins over a same-named fallback input.  The
        caller supplies transformed adapter values explicitly; this method only
        verifies that every document key has a declared destination and copies
        it to the SDK keyword selected by this contract.
        """
        values = dict(document or {})
        # A bound invocation can be passed through a second domain adapter
        # (for example a generated dashboard handler adds its positional
        # resource and then calls this helper once more).  Context values are
        # not admitted from the request document, but once they have crossed
        # the contract boundary they are safe and must remain idempotent.
        bound_context_names = set(self.context_bindings) & set(values)
        unknown = sorted(set(values) - self.declared_input_names - bound_context_names)
        if unknown and self.extensibility == "closed":
            raise ContractBindingError(
                f"Input field(s) have no declared binding for '{self.command_id}': "
                f"{', '.join(unknown)}"
            )
        bound: dict[str, Any] = {
            self.input_bindings.get(name, name): value
            for name, value in values.items()
            if name not in bound_context_names
        }
        for name in bound_context_names:
            destination = self.context_bindings[name]
            bound[destination] = values[name]
        undeclared_context = sorted(set(context) - set(self.context_bindings))
        if undeclared_context:
            raise ContractBindingError(
                f"Context field(s) have no declared binding for '{self.command_id}': "
                f"{', '.join(undeclared_context)}"
            )
        for name, value in context.items():
            context_destination = self.context_bindings.get(name)
            # The explicit context check above makes this assertion a useful
            # guard if the implementation changes the mapping representation.
            assert context_destination is not None
            bound[context_destination] = value
        return bound


def _input_schema(
    command_id: str,
    record: Mapping[str, Any],
    fields: tuple[FieldSpec, ...],
    positionals: tuple[PositionalSpec, ...],
) -> Mapping[str, Any] | None:
    """Build the contract's closed input schema from its fields."""
    if not fields:
        return MappingProxyType(
            {
                "type": "object",
                "properties": MappingProxyType({}),
                "required": (),
                "additionalProperties": False,
            }
        )
    properties: dict[str, Any] = {}
    operation_ids = tuple(str(item) for item in record.get("operation_ids", ()))
    body_schema = openapi_body_schema_for(operation_ids)
    for field in fields:
        if field.name == "body" and is_opaque_mapping(field.annotation) and body_schema is not None:
            properties[field.name] = body_schema
        else:
            properties[field.name] = json_schema(field.annotation, field.name)
    fallbacks = {item.falls_back_to_field for item in positionals if item.falls_back_to_field}
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": [
            field.name for field in fields if field.required and field.name not in fallbacks
        ],
        "additionalProperties": False,
    }
    if command_id == "batch.create-spec":
        properties = cast(dict[str, Any], schema["properties"])
        schema["oneOf"] = [
            {
                "required": ["source_id", "mapping"],
                "properties": properties,
                "additionalProperties": False,
            },
            {
                "required": ["file_id"],
                "properties": properties,
                "additionalProperties": False,
            },
        ]
    return cast(Mapping[str, Any], _freeze(schema))


# These are the first reviewed domain adapters.  Keeping the catalog explicit
# makes a dropped field visible in tests instead of silently forwarding every
# SDK argument by reflection.  The resolver remains generic for discovery.
_PILOT_ADAPTER_INPUTS: dict[str, frozenset[str]] = {
    "file.upload": frozenset({"files"}),
    "view.transform.math": frozenset({"condition"}),
    "view.transform.lookup": frozenset(),
    "dashboard.create": frozenset({"intent"}),
    "dashboard.source.list": frozenset(),
}

# Local commands do not have a public SDK signature to introspect.  They still
# need the same closed admission contract as API-backed commands: otherwise a
# bespoke handler can accidentally accept an arbitrary document (or silently
# ignore a misspelled field) while discovery reports no useful request shape.
# Keep this catalog explicit and deliberately boring.  Command-specific
# conversions remain in the named handlers, while these fields are the only
# values that may cross the structured-input boundary.
_LOCAL_CONTRACT_FIELDS: dict[str, tuple[FieldSpec, ...]] = {
    "auth.login": (
        FieldSpec("api_key", required=True, annotation=str),
        FieldSpec("api_secret", required=True, annotation=str),
        FieldSpec("workspace_id", required=True, annotation=int),
        FieldSpec("server_prefix", required=False, annotation=str | None, default=None),
    ),
    "completion.install": (
        FieldSpec("shell", required=False, annotation=str | None, default=None),
    ),
    "completion.show": (FieldSpec("shell", required=False, annotation=str | None, default=None),),
    "skill.install": (
        FieldSpec("agents", required=False, annotation=list[str] | None, default=None),
        FieldSpec("scope", required=False, annotation=str, default="user"),
        FieldSpec("force", required=False, annotation=bool, default=False),
    ),
    "log.path": (),
    "log.tail": (
        FieldSpec("days", required=False, annotation=int, default=1),
        FieldSpec("limit", required=False, annotation=int, default=50),
        FieldSpec("errors_only", required=False, annotation=bool, default=False),
        FieldSpec("command_id", required=False, annotation=str | None, default=None),
        FieldSpec("run_id", required=False, annotation=str | None, default=None),
    ),
    "skill.list": (),
    "skill.path": (
        FieldSpec("agents", required=False, annotation=list[str] | None, default=None),
        FieldSpec("scope", required=False, annotation=str, default="user"),
    ),
    "skill.uninstall": (
        FieldSpec("agents", required=False, annotation=list[str] | None, default=None),
        FieldSpec("scope", required=False, annotation=str, default="user"),
    ),
    "skill.update": (
        FieldSpec("agents", required=False, annotation=list[str] | None, default=None),
        FieldSpec("scope", required=False, annotation=str, default="user"),
        FieldSpec("force", required=False, annotation=bool, default=False),
    ),
}

_RELEASE_BATCH_SPEC_FIELDS = (
    FieldSpec("source_id", required=False, annotation=int | None, default=None),
    FieldSpec(
        "mapping",
        required=False,
        annotation=list[ColumnNameMapping] | list[ColumnIdMapping] | None,
        default=None,
    ),
    FieldSpec("validate_only", required=False, annotation=bool, default=False),
    FieldSpec("delete_source_ds", required=False, annotation=bool, default=False),
    FieldSpec("new_ds_details", required=False, annotation=NewDsDetails | None, default=None),
    FieldSpec("file_id", required=False, annotation=int | None, default=None),
    FieldSpec(
        "projected_source_schema",
        required=False,
        annotation=list[ProjectedSourceColumn] | None,
        default=None,
    ),
)

# The remaining S1 commands are intentionally closed zero-input commands.  A
# command may still receive ordinary positional/context values; those are
# represented by ``positionals`` and never become structured-input keys.
_LOCAL_COMMANDS = frozenset(
    {
        "auth.login",
        "auth.logout",
        "auth.status",
        "capability.find",
        "capability.get",
        "capability.list",
        "completion.install",
        "completion.show",
        "config.get",
        "config.list",
        "config.path",
        "config.set",
        "context.project.clear",
        "context.project.status",
        "context.project.use",
        "dataset.find",
        "doctor",
        "folder.find",
        "log.path",
        "log.tail",
        "schema.find",
        "schema.get",
        "schema.list",
        "skill.install",
        "skill.list",
        "skill.path",
        "skill.uninstall",
        "skill.update",
        "upgrade",
        "version",
    }
)

# C2/S2 is the first API-backed family migrated after the local/auth pilot.
# Keep the route set explicit: a family is not considered migrated merely
# because a manifest record happens to have an SDK signature.  The S2 handlers
# consume ``Invocation.bound_input`` and therefore use this same contract for
# admission, schema discovery, and SDK-bound values.
S2_COMMANDS = frozenset(
    {
        "addon.connector.add",
        "addon.connector.remove",
        "addon.list",
        "addon.storage.add",
        "addon.storage.remove",
        "addon.user.add",
        "addon.user.remove",
        "annotation.comment.add",
        "annotation.create",
        "annotation.delete",
        "annotation.list",
        "annotation.update",
        "browse.folder",
        "browse.project",
        "browse.root",
        "browse.workspace",
        "dataset.bulk-delete",
        "dataset.bulk-update",
        "dataset.create",
        "dataset.create-from-pdf",
        "dataset.data",
        "dataset.delete",
        "dataset.file-settings.get",
        "dataset.file-settings.undo",
        "dataset.file-settings.update",
        "dataset.get",
        "dataset.list",
        "dataset.rename",
        "dataset.restore",
        "dataset.trash",
        "dataset.update",
        "file.bulk-delete",
        "file.delete",
        "file.extract-sheets",
        "file.get",
        "file.list",
        "file.set-password",
        "file.update",
        "file.upload",
        "file.upload-folder",
        "folder.bulk-delete",
        "folder.create",
        "folder.delete",
        "folder.get",
        "folder.list",
        "folder.move",
        "folder.root",
        "folder.trash",
        "folder.update",
        "notification.delete",
        "notification.delete-batch",
        "notification.list",
        "notification.update",
        "notification.update-batch",
        "project.bulk-delete",
        "project.bulk-update",
        "project.checkpoint.list",
        "project.create",
        "project.data-check.list",
        "project.delete",
        "project.get",
        "project.list",
        "project.pending-changes",
        "project.publish-credentials",
        "project.resource-dependencies",
        "project.resource-status",
        "project.sample-flow",
        "project.update",
        "project.user.add",
        "project.user.remove",
        "project.user.update",
        "trash.add",
        "trash.list",
        "trash.restore",
        "workspace.accept-invite",
        "workspace.app-usage",
        "workspace.check-expression",
        "workspace.create",
        "workspace.delete",
        "workspace.get",
        "workspace.list",
        "workspace.llm-task",
        "workspace.reactivate",
        "workspace.segment.list",
        "workspace.segment.update",
        "workspace.storage-breakdown",
        "workspace.update",
        "workspace.user.add",
        "workspace.user.get",
        "workspace.user.list",
        "workspace.user.remove",
        "workspace.user.remove-batch",
        "workspace.user.update",
        "workspace.user.update-batch",
    }
)

# ``ViewExport`` destination helpers intentionally expose ``**kwargs`` for
# legacy trigger controls.  The CLI keeps those helpers typed and closed at
# its boundary so discovery and strict admission show the reviewed destination
# shape instead of an unbounded dictionary.
_SPECIAL_EXPORT_REQUIRED: dict[str, frozenset[str]] = {
    "view.export.dataset": frozenset({"dataset_name"}),
    "view.export.managed-s3": frozenset(),
    "view.export.azure-blob": frozenset(
        {"storage_account_name", "tenant_id", "client_id", "client_secret", "container_name"}
    ),
    "view.export.bigquery": frozenset({"selected_profile", "selected_identity", "table"}),
    "view.export.elasticsearch": frozenset({"host", "username", "password", "index"}),
    "view.export.email": frozenset({"emails"}),
    "view.export.ftp": frozenset({"domain", "directory", "file", "username", "password"}),
    "view.export.mssql": frozenset({"host", "port", "database", "table", "username", "password"}),
    "view.export.mysql": frozenset({"host", "port", "database", "table", "username", "password"}),
    "view.export.onedrive": frozenset({"tenant_id", "client_id", "client_secret", "user_id"}),
    "view.export.postgres": frozenset(
        {"host", "port", "database", "table", "username", "password"}
    ),
    "view.export.powerbi": frozenset({"username", "password", "client_id", "dataset", "table"}),
    "view.export.redshift": frozenset(
        {"host", "port", "database", "table", "username", "password"}
    ),
    "view.export.rest": frozenset({"base_url", "endpoint_path"}),
    "view.export.sftp": frozenset({"host", "username"}),
    "view.export.sharepoint": frozenset({"tenant_id", "client_id", "client_secret", "site_url"}),
    "view.export.tableau": frozenset({"server_url", "token_name", "token_secret"}),
}
_SPECIAL_EXPORT_COMMON: dict[str, Any] = {
    "dataset_id": int,
    "trigger_type": Any,
    "run_immediately": bool,
    "validate_only": bool,
    "end_of_pipeline": bool,
    "additional_properties": dict[str, Any],
    "condition": Any,
}


def _special_export_fields(command_id: str, spec: ArgSpec | None) -> tuple[FieldSpec, ...] | None:
    required = _SPECIAL_EXPORT_REQUIRED.get(command_id)
    if required is None:
        return None
    declared = list(spec.fields if spec is not None else ())
    declared_names = {field.name for field in declared}
    for name, annotation in _SPECIAL_EXPORT_COMMON.items():
        if name not in declared_names:
            declared.append(FieldSpec(name=name, required=False, annotation=annotation))
    return tuple(declared)


# These family sets are derived from the checked-in command manifest rather
# than copied from the workbook.  They make the admission boundary closed for
# the completed C2 slices while leaving S5 (exports/connectors) available for
# its owner to migrate independently. S7 publishes its shared catalog below;
# its command handlers remain owned by that worker.
# The prefixes are intentionally narrow and the resulting counts are asserted
# by the route-ledger tests.
S3_COMMANDS = frozenset(
    record["command_id"]
    for record in load_commands()
    if str(record["command_id"]).startswith("view.")
    and not str(record["command_id"]).startswith("view.export.")
    and not str(record["command_id"]).startswith(
        ("view.checkpoint.", "view.draft.", "view.pipeline.", "view.task.", "view.version.")
    )
)
S4_COMMANDS = frozenset(
    record["command_id"]
    for record in load_commands()
    if str(record["command_id"]).split(".", 1)[0]
    in {"batch", "job", "parameter", "snippet", "workflow"}
    or str(record["command_id"]).startswith(
        ("view.checkpoint.", "view.draft.", "view.pipeline.", "view.task.", "view.version.")
    )
)
S6_COMMANDS = frozenset(
    record["command_id"]
    for record in load_commands()
    if str(record["command_id"]).split(".", 1)[0] in {"dashboard", "data-app", "report", "template"}
)
# S7 owns these remaining families.  Exporting the manifest-derived inventory
# here keeps the shared interface available to its worker without claiming
# that this slice has admitted or bound those handlers yet.
S7_COMMANDS = frozenset(
    record["command_id"]
    for record in load_commands()
    if str(record["command_id"]).split(".", 1)[0]
    in {
        "activity",
        "agent",
        "ai",
        "automation",
        "billing",
        "client-app",
        "schedule",
        "support",
        "user",
    }
    # The S7 ledger is a frozen 104-route cohort.  REL-480 was added later
    # and has its own focused contract tests; do not silently change this
    # cohort denominator when new AI bindings land.
    and str(record["command_id"]) != "ai.retention.condition"
)

# A small number of S7 SDK methods intentionally expose a ``**kwargs``
# extension point.  The CLI still keeps their input boundary closed: these
# are the reviewed filter/profile fields that the corresponding public API
# accepts.  Keeping the declarations here makes schema generation, strict
# admission, and handler binding agree instead of treating every arbitrary
# keyword as valid.
_S7_ADDITIONAL_INPUT_FIELDS: dict[str, tuple[FieldSpec, ...]] = {
    "activity.list": (
        FieldSpec("project_id", required=False, annotation=int | None, default=None),
        FieldSpec("workspace_id", required=False, annotation=int | None, default=None),
        FieldSpec("categories", required=False, annotation=list[Any] | None, default=None),
        FieldSpec("activities", required=False, annotation=list[Any] | None, default=None),
        FieldSpec("resource_id", required=False, annotation=Any, default=None),
        FieldSpec("result", required=False, annotation=str | None, default=None),
        FieldSpec("start_time", required=False, annotation=str | None, default=None),
        FieldSpec("end_time", required=False, annotation=str | None, default=None),
        FieldSpec("origin", required=False, annotation=str | None, default=None),
        FieldSpec("user_ids", required=False, annotation=list[Any] | None, default=None),
        FieldSpec("parent_id", required=False, annotation=int | None, default=None),
        FieldSpec("search_text", required=False, annotation=str | None, default=None),
    ),
    "activity.export": (
        FieldSpec("workspace_id", required=False, annotation=int | None, default=None),
        FieldSpec("start_time", required=False, annotation=str | None, default=None),
        FieldSpec("end_time", required=False, annotation=str | None, default=None),
        FieldSpec("categories", required=False, annotation=list[Any] | None, default=None),
        FieldSpec("activities", required=False, annotation=list[Any] | None, default=None),
        FieldSpec("user_ids", required=False, annotation=list[Any] | None, default=None),
    ),
    "user.preference.update": (
        # PreferencesPatchRequest: replace ops on dotted paths rooted at
        # GLOBAL or WORKSPACE_PREFERENCES.
        FieldSpec("patch", required=False, annotation=list[Any] | None, default=None),
    ),
    "user.update": (
        FieldSpec("name", required=False, annotation=str | None, default=None),
        FieldSpec("email", required=False, annotation=str | None, default=None),
    ),
}
CONTRACT_BOUND_COMMANDS = frozenset(
    S2_COMMANDS | S3_COMMANDS | S4_COMMANDS | S6_COMMANDS | S7_COMMANDS
)

# The five reviewed adapter shapes remain separately named for compatibility
# with existing pilot tests and release notes.
PILOT_COMMANDS = frozenset(_PILOT_ADAPTER_INPUTS)
LOCAL_COMMANDS = _LOCAL_COMMANDS


@cache
def resolve_command_contract(command_id: str) -> ResolvedCommandContract | None:
    """Resolve and cache an immutable contract for a manifest command."""
    record = command_by_id(command_id)
    if record is None:
        return None
    symbol = str(record["sdk_symbol"]) if record.get("sdk_symbol") else None
    spec: ArgSpec | None = arg_spec(symbol) if symbol else None
    positions = tuple(resolve_positionals(command_id))
    is_local = command_id in _LOCAL_COMMANDS
    excluded = (
        frozenset()
        if is_local
        else excluded_input_fields(command_id) | handler_owned_fields(command_id)
    )
    special_fields = _special_export_fields(command_id, spec)
    if command_id == "batch.create-spec":
        special_fields = _RELEASE_BATCH_SPEC_FIELDS
    local_fields = _LOCAL_CONTRACT_FIELDS.get(command_id, ()) if is_local else None
    fields = tuple(
        field
        for field in (
            local_fields
            if local_fields is not None
            else (
                special_fields
                if special_fields is not None
                else (spec.fields if spec is not None else ())
            )
        )
        if field.name not in excluded
    )
    # Transform handlers accept the exact parent dataset as resource context.
    # Invocation.prepare_input removes this field only while validating the
    # SDK-shaped document, then restores it for the handler/service boundary;
    # expose it in discovery so agents can provide the same safe binding they
    # can already use at runtime.
    if accepts_resource_dataset(command_id) and "dataset_id" not in {
        field.name for field in fields
    }:
        fields += (FieldSpec("dataset_id", required=False, annotation=int | None, default=None),)
    additional_fields = _S7_ADDITIONAL_INPUT_FIELDS.get(command_id, ())
    declared_names = {field.name for field in fields}
    fields += tuple(field for field in additional_fields if field.name not in declared_names)
    bindings = MappingProxyType({field.name: field.name for field in fields})
    # Positionals fill SDK parameters only when they are not dual-sourced.  A
    # fallback positional stays an input binding and is overlaid by ``bind``
    # when its caller supplies the explicit positional value.
    context_values = {item.name: item.fills_sdk_param or item.name for item in positions}
    # Transform target parents are resource identity, not View method
    # arguments. Invocation admits this field around normal SDK validation so
    # the service can resolve the exact parent; declaring it as context keeps
    # the subsequent shared bind idempotent after that protected preflight.
    if accepts_resource_dataset(command_id):
        context_values["dataset_id"] = "dataset_id"
    context = MappingProxyType(context_values)
    extensibility = (
        "closed"
        if is_local or command_id in CONTRACT_BOUND_COMMANDS or special_fields is not None
        else (
            "closed"
            if is_closed_zero_input(command_id)
            else "open" if spec is None or spec.accepts_extra else "closed"
        )
    )
    schema = (
        None if extensibility == "open" else _input_schema(command_id, record, fields, positions)
    )
    return ResolvedCommandContract(
        command_id=command_id,
        sdk_symbol=symbol,
        fields=fields,
        positionals=positions,
        input_bindings=bindings,
        adapter_inputs=_PILOT_ADAPTER_INPUTS.get(command_id, frozenset()),
        context_bindings=context,
        input_schema=schema,
        extensibility=extensibility,
        mutation_class=record.get("mutation_class"),
        confirmation=record.get("confirmation"),
        wait_policy=record.get("wait_policy"),
        result_model=record.get("result_model"),
        capability_identity=tuple(str(item) for item in record.get("operation_ids", ())),
    )


def bind_command_inputs(
    contract_command_id: str,
    document: Mapping[str, Any] | None = None,
    **context: Any,
) -> dict[str, Any]:
    """Resolve a command contract and bind its supplied values."""
    contract = resolve_command_contract(contract_command_id)
    if contract is None:
        raise ContractBindingError(f"No command contract exists for '{contract_command_id}'.")
    return contract.bind(document, **context)


# Short aliases make the pilot's call sites read naturally while retaining one
# canonical public resolver name for schema/tests.
resolved_command_contract = resolve_command_contract
bind_inputs = bind_command_inputs
