#!/usr/bin/env python3
"""Load the reviewed SDK-symbol -> command catalog and CLI-only command specs.

The catalog source (``spec/manifests/sdk-catalog.source.yaml``) is a committed,
primary-reviewed build input. A few catalog command ids are normalized to the
canonical CLI scheme used across the manifests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SPEC = Path(__file__).resolve().parent.parent / "spec"
CATALOG_SOURCE = SPEC / "manifests" / "sdk-catalog.source.yaml"

# Normalize catalog command ids to the canonical CLI scheme.
CATALOG_COMMAND_REMAP = {
    "project.browse": "browse.project",
}

# Underlying OpenAPI operation(s) and HTTP method for SDK-convenience commands
# that do not map 1:1 to a single operation (they share an operation).
EXTRA_OP_HINTS: dict[str, dict[str, Any]] = {
    # All typed transforms add one pipeline task.
    **{
        f"view.transform.{name}": {"operation_ids": ["AddTask"], "method": "POST"}
        for name in (
            "add-column delete-columns copy-columns combine-columns convert-type filter "
            "set-values math small-large text replace bulk-replace split substring "
            "extract-date date-diff increment-date fill-missing limit-rows discard-duplicates "
            "unnest pivot window crosstab join lookup json-extract ai generate-sql add-sql"
        ).split()
    },
    # Draft verbs execute one draft-mode command endpoint.
    **{
        f"view.draft.{name}": {"operation_ids": ["ExecutePipelineDraftCommand"], "method": "POST"}
        for name in ("enter submit discard status auto-run").split()
    },
    "view.export.csv": {"operation_ids": ["AddExport"], "method": "POST"},
    "view.pipeline.wait": {"operation_ids": [], "method": "GET"},
    "job.wait": {"operation_ids": ["GetJob"], "method": "GET"},
    "job.wait-many": {"operation_ids": ["GetJobs"], "method": "GET"},
    "dataset.rename": {"operation_ids": ["UpdateDataset"], "method": "PATCH"},
    "file.extract-sheets": {"operation_ids": ["UpdateFileConfigs"], "method": "PATCH"},
    "file.set-password": {"operation_ids": ["UpdateFileConfigs"], "method": "PATCH"},
    "file.upload-folder": {"operation_ids": ["CreateFileDataset"], "method": "POST"},
    "folder.root": {"operation_ids": ["ListFolders"], "method": "GET"},
    "project.get": {"operation_ids": [], "method": "GET"},
    "user.change-password": {"operation_ids": ["UpdateUser"], "method": "PATCH"},
    "workspace.user.get": {"operation_ids": [], "method": "GET"},
    "addon.list": {"operation_ids": [], "method": "GET"},
}

# CLI-only commands: no OpenAPI operation and no Mammoth transport. They are
# handled locally (auth, config, context, diagnostics, discovery, skill).
CLI_ONLY_COMMANDS: dict[str, dict[str, Any]] = {
    "auth.login": {
        "sdk_symbol": "mammoth_cli.context.auth.login",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local credential storage; no mutating server call.",
    },
    "auth.logout": {
        "sdk_symbol": "mammoth_cli.context.auth.logout",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local credential removal.",
    },
    "auth.status": {
        "sdk_symbol": "mammoth_cli.context.auth.status",
        "mutation_class": "read",
        "live_exemption_reason": "Local credential status.",
    },
    "config.get": {
        "sdk_symbol": "mammoth_cli.context.config.get",
        "mutation_class": "read",
        "live_exemption_reason": "Local configuration read.",
    },
    "config.set": {
        "sdk_symbol": "mammoth_cli.context.config.set",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local configuration write.",
    },
    "config.list": {
        "sdk_symbol": "mammoth_cli.context.config.list",
        "mutation_class": "read",
        "live_exemption_reason": "Local configuration read.",
        "pagination_policy": "none",
    },
    "config.path": {
        "sdk_symbol": "mammoth_cli.context.config.path",
        "mutation_class": "read",
        "live_exemption_reason": "Local configuration path.",
    },
    "context.project.status": {
        "sdk_symbol": "mammoth_cli.context.project.status",
        "mutation_class": "read",
        "live_exemption_reason": "Local project context read.",
    },
    "context.project.use": {
        "sdk_symbol": "mammoth_cli.context.project.use",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local project context write.",
    },
    "context.project.clear": {
        "sdk_symbol": "mammoth_cli.context.project.clear",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local project context clear.",
    },
    "doctor": {
        "sdk_symbol": "mammoth_cli.commands.doctor.run",
        "mutation_class": "read",
        "live_exemption_reason": "Diagnostic; safe read-only checks.",
    },
    "capability.list": {
        "sdk_symbol": "mammoth_cli.commands.capability.list_",
        "mutation_class": "read",
        "live_exemption_reason": "Local manifest read.",
        "pagination_policy": "none",
    },
    "capability.get": {
        "sdk_symbol": "mammoth_cli.commands.capability.get",
        "mutation_class": "read",
        "live_exemption_reason": "Local manifest read.",
    },
    "schema.list": {
        "sdk_symbol": "mammoth_cli.commands.schema.list_",
        "mutation_class": "read",
        "live_exemption_reason": "Local manifest read.",
        "pagination_policy": "none",
    },
    "schema.get": {
        "sdk_symbol": "mammoth_cli.commands.schema.get",
        "mutation_class": "read",
        "live_exemption_reason": "Local manifest read.",
    },
    "completion.install": {
        "sdk_symbol": "mammoth_cli.commands.completion.install",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local shell completion install.",
    },
    "completion.show": {
        "sdk_symbol": "mammoth_cli.commands.completion.show",
        "mutation_class": "read",
        "live_exemption_reason": "Local shell completion output.",
    },
    "skill.install": {
        "sdk_symbol": "mammoth_cli.skills.installer.install",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local agent-skill install.",
    },
    "skill.list": {
        "sdk_symbol": "mammoth_cli.skills.installer.list_",
        "mutation_class": "read",
        "live_exemption_reason": "Local agent-skill list.",
        "pagination_policy": "none",
    },
    "skill.path": {
        "sdk_symbol": "mammoth_cli.skills.installer.path",
        "mutation_class": "read",
        "live_exemption_reason": "Local agent-skill path.",
    },
    "skill.update": {
        "sdk_symbol": "mammoth_cli.skills.installer.update",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local agent-skill update.",
    },
    "skill.uninstall": {
        "sdk_symbol": "mammoth_cli.skills.installer.uninstall",
        "mutation_class": "benign_mutation",
        "live_exemption_reason": "Local agent-skill uninstall.",
    },
    "version": {
        "sdk_symbol": "mammoth_cli.commands.meta.version",
        "mutation_class": "read",
        "live_exemption_reason": "Local version output.",
    },
}


def load_sdk_catalog() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(CATALOG_SOURCE.read_text(encoding="utf-8"))
    catalog: dict[str, dict[str, Any]] = {}
    for record in data.get("sdk_methods", []):
        record = dict(record)
        for key in ("canonical_command", "alias_of"):
            value = record.get(key)
            if value in CATALOG_COMMAND_REMAP:
                record[key] = CATALOG_COMMAND_REMAP[value]
        catalog[record["sdk_symbol"]] = record
    return catalog


if __name__ == "__main__":
    cat = load_sdk_catalog()
    print("catalog rows:", len(cat))
    print("extra op hints:", len(EXTRA_OP_HINTS))
    print("cli-only commands:", len(CLI_ONLY_COMMANDS))
