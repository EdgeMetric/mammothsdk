"""Command input fields that the CLI, rather than the SDK call, supplies."""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.positionals import resolve_positionals

_HANDLER_OWNED_FIELDS: dict[str, frozenset[str]] = {
    # Skill handlers deliberately derive filesystem roots from the running
    # process and generate their own backup timestamp.  User input must not
    # claim to control values that the handlers replace or omit.
    "skill.install": frozenset({"home", "cwd", "timestamp"}),
    "skill.update": frozenset({"home", "cwd", "timestamp"}),
    "skill.uninstall": frozenset({"home", "cwd"}),
    "skill.path": frozenset({"home", "cwd"}),
    # ``job get`` is an immediate status read; only wait commands implement
    # the CLI's timeout/polling behavior.
    "job.get": frozenset({"timeout"}),
    # ``PipelineAPI.get_draft_status`` carries a legacy ``dataset_id`` alongside
    # the ``dataview_id`` the handler forwards from the view positional; the
    # handler never reads it, so it must not be advertised as an --input field.
    "view.draft.status": frozenset({"dataset_id"}),
    # These handlers supply the SDK dataview_id from the VIEW_ID positional.
    "view.exportable-config.get": frozenset({"dataview_id"}),
    "view.exportable-config.apply": frozenset({"dataview_id"}),
}

# CLI-only commands whose complete request is carried by positionals/context.
# This is the single source used by both resolved contracts and runtime
# admission; an unresolved Python signature must not make these commands open.
_CLOSED_ZERO_INPUT_COMMANDS = frozenset({"config.get"})


#: Extra ``--input`` fields to weave into a command's generated ``agent_example``.
#: A few commands enforce a runtime "exactly one of" / identifier requirement that
#: the SDK signature marks optional (so the auto-generated example, which only fills
#: signature-required fields, omits it and is not actually runnable as shown). Each
#: value here is a genuine, accepted --input field so the documented example both
#: validates against the input schema and works when run.
_EXAMPLE_INPUT_HINTS: dict[str, dict[str, Any]] = {
    # Every field is optional; the useful call narrows to failures.
    "log.tail": {"errors_only": True, "limit": 20},
    # The signature marks the target column and the condition optional, but a
    # SET with neither ``existing_column`` nor ``new_column`` has no target and
    # an unconditional SET rewrites every row; show the verified conditional form.
    "view.transform.set-values": {
        "existing_column": "Status",
        "condition": {"column": "Status", "operator": "IS_EMPTY"},
    },
    # The backend requires integer resource ids ("resource_ids must be
    # comma-separated integers"); the SDK annotation is a plain list[str].
    "project.resource-dependencies": {"resource_ids": [456]},
    "view.export.azure-blob": {
        "storage_account_name": "storage-account",
        "tenant_id": "tenant-id",
        "client_id": "client-id",
        "client_secret": "replace-with-secret",
        "container_name": "exports",
    },
    "view.export.bigquery": {
        "selected_profile": {},
        "selected_identity": {},
        "table": "exports",
    },
    "view.export.dataset": {"dataset_name": "snapshot"},
    "view.export.elasticsearch": {
        "host": "elastic.example",
        "username": "agent",
        "password": "replace-with-secret",
        "index": "exports",
    },
    "view.export.email": {"emails": ["recipient@example.com"]},
    "view.export.ftp": {
        "domain": "ftp.example",
        "directory": "/exports",
        "file": "report.csv",
        "username": "agent",
        "password": "replace-with-secret",
    },
    "view.export.managed-s3": {"file_name": "report.csv"},
    "view.export.mssql": {
        "host": "db.example",
        "port": 1433,
        "database": "analytics",
        "table": "exports",
        "username": "agent",
        "password": "replace-with-secret",
    },
    "view.export.mysql": {
        "host": "db.example",
        "port": 3306,
        "database": "analytics",
        "table": "exports",
        "username": "agent",
        "password": "replace-with-secret",
    },
    "view.export.onedrive": {
        "tenant_id": "tenant-id",
        "client_id": "client-id",
        "client_secret": "replace-with-secret",
        "user_id": "user-id",
    },
    "view.export.postgres": {
        "host": "db.example",
        "port": 5432,
        "database": "analytics",
        "table": "exports",
        "username": "agent",
        "password": "replace-with-secret",
    },
    "view.export.powerbi": {
        "username": "agent",
        "password": "replace-with-secret",
        "client_id": "client-id",
        "dataset": "dataset",
        "table": "exports",
    },
    "view.export.redshift": {
        "host": "db.example",
        "port": 5439,
        "database": "analytics",
        "table": "exports",
        "username": "agent",
        "password": "replace-with-secret",
    },
    "view.export.rest": {"base_url": "https://api.example", "endpoint_path": "/records"},
    "view.export.sftp": {"host": "sftp.example", "username": "agent"},
    "view.export.sharepoint": {
        "tenant_id": "tenant-id",
        "client_id": "client-id",
        "client_secret": "replace-with-secret",
        "site_url": "https://sharepoint.example/site",
    },
    "view.export.tableau": {
        "server_url": "https://tableau.example",
        "token_name": "token",
        "token_secret": "replace-with-secret",
    },
    # AddonsAPI.add_connector/remove_connector require exactly one of
    # ``connector_id``/``connector_ids``; both are optional in the signature.
    "addon.connector.add": {"connector_id": 42},
    "addon.connector.remove": {"connector_id": 42},
    # The generic SDK types cannot express the creation-type-specific dataset
    # shape. Use the public sample CSV so help and generated references show a
    # request a new customer can understand and run.
    "dataset.create": {
        "ds_creation_type": "weburl",
        "dataset_spec": {"url": "https://sampledata.mammoth.io/Multi-Store_Retail_Sales.csv"},
    },
    # project user update targets a specific member: the handler requires ``role``
    # (auto-filled) plus one of ``user_id``/``invite_id`` to say *which* member.
    "project.user.update": {"user_id": 123},
    # Blank dashboard creation requires a typed params envelope. Keep the
    # generated destructive example runnable with the explicit approval flag.
    "dashboard.create-blank": {"params": {"dataview_id": 1}},
    # The draft/published data routes take a WidgetDataSpec keyed by the
    # widget UUID (read it from ``dashboard canvas get``), not a SQL string.
    "dashboard.data.draft": {"widget_id": "550e8400-e29b-41d4-a716-446655440000"},
    "dashboard.data.published": {"widget_id": "550e8400-e29b-41d4-a716-446655440000"},
    # ``descriptor`` is a baked/1 QueryDescriptor discriminated by ``kind``
    # (group | scalar | rate | detail | options | range); an empty object is
    # rejected. A scalar row count runs against any dashboard.
    "dashboard.query": {"body": {"params": {"descriptor": {"kind": "scalar", "agg": "count"}}}},
    # ``path`` is a bare field name (title | intent | theme | pages | filters),
    # not a JSON pointer, and an ``intent`` value must be at least 10 chars; a
    # title rename is the smallest patch that runs.
    "dashboard.update": {
        "patch": [{"op": "replace", "path": "title", "value": "Renamed dashboard"}]
    },
    # Contracts observed on release (write sweep 2026-09-18): the SQL route
    # requires dataset_id; conditional-format deletion is per rule; bulk
    # dataset deletion takes explicit ids; folder moves take integer resource
    # ids and a destination folder id or "root"; a project rename needs a field.
    "ai.sql.generate": {"dataset_id": 456},
    # UnifiedPromptSpec: the params shape follows suggestion_type.
    "ai.suggestion.list": {
        "suggestion_type": "generate_task",
        "params": {"prompt": "Filter rows where Price > 100"},
        "dataset_id": 456,
        "dataview_id": 123,
    },
    "view.ai.profile": {"dataset_id": 456, "action": "insights"},
    "connector.query.generate": {"query": "Total sales for January"},
    # HighlightEntry: cf_type + payload{FORMAT, CONDITION keyed by internal
    # column name}; the create response and ``conditional-format list`` carry
    # the generated rule_id that delete-all needs.
    "view.conditional-format.create": {
        "rule": {
            "cf_type": "RULE",
            "payload": {
                "FORMAT": {
                    "name": "Flag open orders",
                    "color": "red",
                    "applies_to": "row",
                    "column_ids": "[]",
                },
                "CONDITION": {"OR": [{"column_1": {"CONTAINS": {"VALUE": ["Open"]}}}]},
            },
        }
    },
    "view.conditional-format.delete-all": {"rule_id": "bca0ff33bd6f8ed1"},
    "dataset.bulk-delete": {"dataset_ids": [456, 457]},
    "folder.move": {"resource_ids": [8024], "target_folder_resource_id": "root"},
    "project.update": {"name": "Renamed project"},
    # ProjectsPatch: role changes across explicitly named projects.
    "project.bulk-update": {
        "patch_data": {
            "patches": [
                {
                    "op": "add",
                    "path": "role",
                    "value": [
                        {
                            "project_id": 456,
                            "user_roles": [{"user_id": 123, "role": "project_analyst"}],
                        }
                    ],
                }
            ]
        }
    },
    "project.user.add": {"user_ids": [123], "role": "project_analyst"},
    "user.preference.update": {
        "patch": [{"op": "replace", "path": "GLOBAL.PREFERENCES.TOP_TABS", "value": []}]
    },
    # Release patch bodies observed on the write sweep; the generic list/dict
    # annotations would otherwise render a placeholder that the backend rejects.
    "view.pipeline.edit": {
        "patches": [{"op": "replace", "path": "auto_run", "value": True}],
    },
    "view.export.publish-db-update": {
        "patch": [{"op": "replace", "path": "credentials", "value": {"odbc_type": "postgres"}}],
    },
    # BatchesPostRequest: every ColumnNameMapping item carries the expected
    # destination type; a bare {src: dst} map cannot satisfy the route.
    "batch.create": {
        "mapping": [
            {
                "source_c_name": "column_1",
                "destination_c_name": "column_1",
                "expected_destination_c_type": "TEXT",
            }
        ]
    },
    # The SQL task reads the view as the quoted table "view:<id>" (or its
    # quoted display name); placeholder names such as ``data`` are rejected.
    "view.transform.add-sql": {
        "query": 'SELECT region, SUM(revenue) AS revenue FROM "view:123" GROUP BY region'
    },
    "view.checkpoint.update": {
        "body": {"patches": [{"op": "command", "path": "approve", "value": None}]},
    },
    # The backend requires a placement ("Data check position must be given");
    # ``pinned_to_end`` is the placement that needs no sequence number.
    "view.checkpoint.create": {
        "body": {
            "checkpoint_name": "Revenue report",
            "checkpoint_type": "alert",
            "pinned_to_end": True,
        },
    },
}


#: Command families whose ``--input`` admits the exact parent ``dataset_id`` as
#: resource identity. It is not a View method argument; the service uses it to
#: fetch the view from its exact parent instead of project-wide discovery,
#: which non-read view commands refuse.
_RESOURCE_DATASET_PREFIXES = ("view.transform.", "view.draft.")


def accepts_resource_dataset(command_id: str) -> bool:
    """Return True when ``dataset_id`` is admitted as resource context for ``command_id``."""
    return command_id.startswith(_RESOURCE_DATASET_PREFIXES)


def example_input_hints(command_id: str) -> dict[str, Any]:
    """Return extra ``--input`` fields to include in the generated example."""
    hints = dict(_EXAMPLE_INPUT_HINTS.get(command_id, {}))
    if accepts_resource_dataset(command_id) and command_id != "view.draft.status":
        # Non-read view commands refuse project-wide parent discovery, so a
        # runnable example must show the exact parent.
        hints.setdefault("dataset_id", 456)
    if command_id == "view.transform.join":
        hints.setdefault("foreign_dataset_id", 457)
    if command_id == "view.transform.lookup":
        hints.setdefault("lookup_dataset_id", 457)
    return hints


def excluded_input_fields(command_id: str) -> frozenset[str]:
    """Return SDK parameters that are not accepted from ``--input``."""
    context_fields = {"project_id", "workspace_id"}
    positional_fields: set[str] = set()
    for item in resolve_positionals(command_id):
        if item.falls_back_to_field is not None:
            # Dual-sourced: the field is still a legitimate --input key.
            continue
        positional_fields.add(item.name)
        if item.fills_sdk_param is not None:
            # The positional also supplies this (differently named) SDK argument.
            positional_fields.add(item.fills_sdk_param)
    return frozenset(context_fields | positional_fields) | _HANDLER_OWNED_FIELDS.get(
        command_id, frozenset()
    )


def handler_owned_fields(command_id: str) -> frozenset[str]:
    """Return only fields consumed, replaced, or intentionally omitted by a handler."""
    return _HANDLER_OWNED_FIELDS.get(command_id, frozenset())


def is_closed_zero_input(command_id: str) -> bool:
    """Whether a command has a reviewed closed, empty input document."""
    return command_id in _CLOSED_ZERO_INPUT_COMMANDS
