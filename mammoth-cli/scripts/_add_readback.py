"""One-off script: inject readback/no_readback into view/dataset/file manifests.

Run once, by hand, to land the D-077 readback declarations for the
CLI-owned families this agent is responsible for (view, dataset, file).
Not part of the build pipeline; delete after the declarations have landed
(``scripts/build_manifests.py`` does not yet know about these fields and
will drop them on its next regeneration -- a follow-up task, not this one).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

COMMANDS_DIR = Path(__file__).resolve().parent.parent / "spec" / "manifests" / "commands"

Declaration = dict[str, Any]

# command_id -> {"readback": {...}} | {"no_readback": "..."}
DECLARATIONS: dict[str, Declaration] = {}


def _data(view_id_source: str) -> Declaration:
    return {
        "readback": {"command": "view.data.get", "ids": {"view_id": view_id_source}, "kind": "data"}
    }


def _data_from_dataset(dataset_id_source: str) -> Declaration:
    return {
        "readback": {
            "command": "view.data.get",
            "ids": {"dataset_id": dataset_id_source},
            "kind": "data",
        }
    }


def _obj(command: str, ids: dict[str, str]) -> Declaration:
    return {"readback": {"command": command, "ids": ids, "kind": "object"}}


def _delivery(command: str, ids: dict[str, str]) -> Declaration:
    return {"readback": {"command": command, "ids": ids, "kind": "delivery"}}


def _no(reason: str) -> Declaration:
    return {"no_readback": reason}


# ---------------------------------------------------------------------------
# view
# ---------------------------------------------------------------------------

_TRANSFORM_COMMANDS = [
    "view.transform.add-column",
    "view.transform.add-sql",
    "view.transform.ai",
    "view.transform.bulk-replace",
    "view.transform.combine-columns",
    "view.transform.convert-type",
    "view.transform.copy-columns",
    "view.transform.crosstab",
    "view.transform.date-diff",
    "view.transform.delete-columns",
    "view.transform.discard-duplicates",
    "view.transform.extract-date",
    "view.transform.fill-missing",
    "view.transform.filter",
    "view.transform.generate-sql",
    "view.transform.increment-date",
    "view.transform.join",
    "view.transform.json-extract",
    "view.transform.limit-rows",
    "view.transform.lookup",
    "view.transform.math",
    "view.transform.pivot",
    "view.transform.rename-columns",
    "view.transform.replace",
    "view.transform.set-values",
    "view.transform.small-large",
    "view.transform.sort",
    "view.transform.split",
    "view.transform.substring",
    "view.transform.text",
    "view.transform.unnest",
    "view.transform.window",
]
for _cmd in _TRANSFORM_COMMANDS:
    DECLARATIONS[_cmd] = _data("positional.0")

# Pipeline/task/draft/version-apply commands: also change the view's real
# data, same shape as a transform.
for _cmd in [
    "view.draft.auto-run",
    "view.draft.discard",
    "view.draft.submit",
    "view.pipeline.edit",
    "view.pipeline.rerun",
    "view.task.add",
    "view.task.delete",
    "view.task.update",
    "view.version.apply",
    "view.ai.generate-data",
]:
    DECLARATIONS[_cmd] = _data("positional.0")

DECLARATIONS["view.create"] = _data("result.id")
DECLARATIONS["view.export.dataset"] = _data("result.view_id")

DECLARATIONS["view.draft.command"] = _no(
    "a draft command stages a change in the draft session; the real view is unchanged "
    "until the draft is submitted"
)
DECLARATIONS["view.draft.enter"] = _no(
    "entering draft mode stages a session; the real view is unchanged until the draft "
    "is submitted"
)

DECLARATIONS["view.active-user.mark"] = _obj("view.active-user.list", {"view_id": "positional.0"})
DECLARATIONS["view.ai.profile"] = _obj("view.ai.generation-info", {"dataview_id": "positional.0"})

DECLARATIONS["view.bulk-delete"] = _obj("view.list", {"dataset_id": "positional.0"})
DECLARATIONS["view.delete"] = _obj("view.list", {})
DECLARATIONS["view.restore"] = _obj("view.get", {"view_id": "positional.0"})
DECLARATIONS["view.trash"] = _obj("view.get", {"view_id": "positional.0"})
DECLARATIONS["view.update"] = _obj("view.get", {"view_id": "positional.0"})

DECLARATIONS["view.checkpoint.create"] = _obj("view.checkpoint.list", {"view_id": "positional.0"})
DECLARATIONS["view.checkpoint.delete"] = _obj("view.checkpoint.list", {"view_id": "positional.0"})
DECLARATIONS["view.checkpoint.update"] = _obj(
    "view.checkpoint.get", {"view_id": "positional.0", "checkpoint_id": "positional.1"}
)

DECLARATIONS["view.conditional-format.create"] = _obj(
    "view.conditional-format.list", {"view_id": "positional.0"}
)
DECLARATIONS["view.conditional-format.delete-all"] = _obj(
    "view.conditional-format.list", {"view_id": "positional.0"}
)
DECLARATIONS["view.conditional-format.update"] = _obj(
    "view.conditional-format.list", {"view_id": "positional.0"}
)

DECLARATIONS["view.data-check.create"] = _obj("view.data-check.list", {"view_id": "positional.0"})
DECLARATIONS["view.data-check.delete"] = _obj("view.data-check.list", {"view_id": "positional.0"})
DECLARATIONS["view.data-check.update"] = _obj(
    "view.data-check.get", {"view_id": "positional.0", "data_check_id": "positional.1"}
)

DECLARATIONS["view.derivative.create"] = _obj("view.derivative.list", {"view_id": "positional.0"})
DECLARATIONS["view.derivative.data"] = _obj("view.derivative.list", {"view_id": "positional.0"})
DECLARATIONS["view.derivative.delete"] = _obj("view.derivative.list", {"view_id": "positional.0"})
DECLARATIONS["view.derivative.update"] = _obj("view.derivative.list", {"view_id": "positional.0"})

DECLARATIONS["view.version.delete"] = _obj("view.version.list", {"view_id": "positional.0"})
DECLARATIONS["view.version.update"] = _obj(
    "view.version.get", {"view_id": "positional.0", "version_id": "positional.1"}
)

DECLARATIONS["view.exportable-config.apply"] = _obj(
    "view.exportable-config.get", {"view_id": "positional.0"}
)

DECLARATIONS["view.export.delete"] = _obj("view.export.list", {"dataview_id": "positional.0"})
DECLARATIONS["view.export.update"] = _obj(
    "view.export.get", {"dataview_id": "positional.0", "export_id": "positional.1"}
)

# External-destination exports: an async job the platform tracks; the CLI
# result carries its trackable id as ``future_id`` (see
# ``mammoth.models.exports.PipelineExportsModificationResp``).
for _cmd in [
    "view.export.azure-blob",
    "view.export.bigquery",
    "view.export.create",
    "view.export.elasticsearch",
    "view.export.email",
    "view.export.ftp",
    "view.export.mssql",
    "view.export.mysql",
    "view.export.onedrive",
    "view.export.postgres",
    "view.export.powerbi",
    "view.export.redshift",
    "view.export.rest",
    "view.export.sftp",
    "view.export.sharepoint",
    "view.export.tableau",
]:
    DECLARATIONS[_cmd] = _delivery("job.get", {"job_id": "result.future_id"})

DECLARATIONS["view.export.csv"] = _no(
    "a CSV export returns a one-time download link that settles synchronously; no CLI "
    "read command can re-fetch it"
)
DECLARATIONS["view.export.managed-s3"] = _no(
    "S3 delivery is external; no CLI read command can confirm the object landed in the bucket"
)
DECLARATIONS["view.export.publish-db"] = _no(
    "ODBC publish-to-database has no CLI read command to confirm the external table was written"
)
DECLARATIONS["view.export.publish-db-update"] = _no(
    "ODBC publish-to-database has no CLI read command to confirm the external table was written"
)

# ---------------------------------------------------------------------------
# dataset
# ---------------------------------------------------------------------------

DECLARATIONS["dataset.create"] = _data_from_dataset("result.dataset_id")
DECLARATIONS["dataset.create-from-pdf"] = _obj("dataset.list", {})
DECLARATIONS["dataset.broken-rows.resolve"] = _obj(
    "dataset.broken-rows.list", {"dataset_id": "positional.0"}
)
DECLARATIONS["dataset.bulk-delete"] = _obj("dataset.list", {})
DECLARATIONS["dataset.bulk-update"] = _obj("dataset.list", {})
DECLARATIONS["dataset.delete"] = _obj("dataset.list", {})
DECLARATIONS["dataset.file-settings.undo"] = _obj(
    "dataset.file-settings.get", {"dataset_id": "positional.0"}
)
DECLARATIONS["dataset.file-settings.update"] = _obj(
    "dataset.file-settings.get", {"dataset_id": "positional.0"}
)
DECLARATIONS["dataset.rename"] = _obj("dataset.get", {"dataset_id": "positional.0"})
DECLARATIONS["dataset.restore"] = _obj("dataset.get", {"dataset_id": "positional.0"})
DECLARATIONS["dataset.trash"] = _obj("dataset.get", {"dataset_id": "positional.0"})
DECLARATIONS["dataset.update"] = _no(
    "this command always rejects with a typed-command redirect before any write happens; "
    "there is no new state to read back"
)

# ---------------------------------------------------------------------------
# file
# ---------------------------------------------------------------------------

DECLARATIONS["file.bulk-delete"] = _obj("file.list", {})
DECLARATIONS["file.delete"] = _obj("file.list", {})
DECLARATIONS["file.extract-sheets"] = _obj("file.get", {"file_id": "positional.0"})
DECLARATIONS["file.set-password"] = _obj("file.get", {"file_id": "positional.0"})
DECLARATIONS["file.update"] = _obj("file.get", {"file_id": "positional.0"})
DECLARATIONS["file.upload"] = _no(
    "the upload result already carries each ready dataset's post-processing view "
    "(columns, row_count, sample rows) from a real read"
)
DECLARATIONS["file.upload-folder"] = _obj("file.list", {})


def _insert_after(
    record: dict[str, Any], anchor_key: str, new_items: Declaration
) -> dict[str, Any]:
    updated: dict[str, Any] = {}
    for key, value in record.items():
        updated[key] = value
        if key == anchor_key:
            updated.update(new_items)
    return updated


def main() -> None:
    for family in ("view", "dataset", "file"):
        path = COMMANDS_DIR / f"{family}.yaml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        commands = doc["commands"]
        missing = []
        for record in commands:
            command_id = record["command_id"]
            if record.get("mutation_class") == "read":
                continue
            declaration = DECLARATIONS.get(command_id)
            if declaration is None:
                missing.append(command_id)
                continue
            new_record = _insert_after(record, "acceptance_evidence", declaration)
            record.clear()
            record.update(new_record)
        if missing:
            raise SystemExit(f"{family}: no declaration authored for {missing}")
        rendered = yaml.safe_dump(
            {"manifest_schema_version": 1, "commands": commands},
            sort_keys=False,
            allow_unicode=True,
            width=100,
        )
        path.write_text(rendered, encoding="utf-8")
        print(f"{family}: wrote {len(commands)} commands")


if __name__ == "__main__":
    main()
