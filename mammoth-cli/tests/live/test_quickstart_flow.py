"""Live end-to-end test of the quickstart story, run against a real tenant.

This walks the exact flow the quickstart doc sells, through the real CLI and a
real Mammoth tenant: create a folder, create a dataset from a sample CSV URL,
wait for its ingestion job, find the default view, run a transformation, preview
the result (asserting the CLI presents DISPLAY column names, never internal
``column_N`` ids), and export the view to a local CSV file. Every disposable
resource it creates is deleted in a ``finally`` so the tenant is left as found.

Marked ``live`` (deselected by default and in CI); skips cleanly without
credentials. Run explicitly::

    set -a; . ../.env.plan; set +a
    pytest tests/live/test_quickstart_flow.py -m live -v
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.testing import make_runner

pytestmark = pytest.mark.live

# The documented sample dataset (plain CSV, retail columns).
_SAMPLE_CSV_URL = "https://sampledata.mammoth.io/Multi-Store_Retail_Sales.csv"

# Response-shape keys parsed here, named to avoid magic strings.
_DATA_KEY = "data"
_JOB_ID_KEY = "job_id"
_JOB_KEY = "job"
_RESPONSE_KEY = "response"
_DS_ID_KEY = "ds_id"
_COLUMNS_KEY = "columns"
_DATAVIEWS_KEY = "dataviews"
_METADATA_KEY = "metadata"
_DISPLAY_NAME_KEY = "display_name"
_TYPE_KEY = "type"
_ID_KEY = "id"
_NUMERIC_TYPE = "NUMERIC"

_INTERNAL_COL_RE = re.compile(r"^column_\d+$")


def _run(args: list[str], env: dict[str, str], *, timeout: float = 180.0) -> dict[str, Any]:
    """Invoke the CLI, assert a clean exit, and return the parsed envelope."""
    result = make_runner().invoke(
        [*args, "--project", env["_PROJECT"], "--output", "json", "--no-input",
         "--job-timeout", str(timeout)],
        env=env,
    )
    assert result.exit_code == 0, f"`{' '.join(args)}` failed: {result.output}"
    envelope: dict[str, Any] = json.loads(result.output)
    assert not envelope.get("error"), envelope.get("error")
    return envelope


def _try(args: list[str], env: dict[str, str]) -> tuple[int, dict[str, Any]]:
    """Invoke the CLI, returning (exit_code, parsed_envelope) without asserting."""
    result = make_runner().invoke(
        [*args, "--project", env["_PROJECT"], "--output", "json", "--no-input"], env=env
    )
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        return result.exit_code, {"raw": result.output}


def test_quickstart_flow_end_to_end(
    live_env: dict[str, str], live_project: str, tmp_path: Path
) -> None:
    env = {**live_env, "_PROJECT": live_project}

    folder_id: int | None = None
    dataset_id: int | None = None
    try:
        # 1) Create a folder.
        folder = _run(["folder", "create", "cli-quickstart-live"], env)[_DATA_KEY]
        folder_id = int(folder[_ID_KEY])

        # 2) Create a dataset from the sample CSV URL -> ingestion job.
        code, created = _try(
            ["dataset", "create", "--input", json.dumps({
                "ds_creation_type": "weburl",
                "dataset_spec": {"url": _SAMPLE_CSV_URL},
            })],
            env,
        )
        if code != 0:
            status = (created.get("error") or {}).get("details", {})
            if isinstance(status, dict) and int(status.get("status_code", 0)) >= 500:
                pytest.skip(f"tenant could not ingest the sample URL (server-side): {created}")
            pytest.fail(f"dataset create failed client-side: {created}")
        job_id = int(created[_DATA_KEY][_JOB_ID_KEY])

        # 3) Wait for the ingestion job; it carries the new dataset id.
        job = _run(["job", "wait", str(job_id)], env)[_DATA_KEY]
        job_body = job.get(_JOB_KEY, job)
        dataset_id = int(job_body[_RESPONSE_KEY][_DS_ID_KEY])

        # 4) Find the dataset's default view.
        views = _run(["view", "list", str(dataset_id)], env)[_DATA_KEY][_DATAVIEWS_KEY]
        assert views, "dataset has no default view"
        view_id = int(views[0][_ID_KEY])

        # 5) Column metadata drives a schema-robust transformation: double the
        #    first NUMERIC column (by its DISPLAY name), else filter non-empty.
        meta = _run(["view", "get", str(view_id)], env)[_DATA_KEY].get(_METADATA_KEY) or []
        numeric = next(
            (c[_DISPLAY_NAME_KEY] for c in meta
             if isinstance(c, dict) and c.get(_TYPE_KEY) == _NUMERIC_TYPE
             and isinstance(c.get(_DISPLAY_NAME_KEY), str)),
            None,
        )
        first_display = next(
            (c[_DISPLAY_NAME_KEY] for c in meta
             if isinstance(c, dict) and isinstance(c.get(_DISPLAY_NAME_KEY), str)),
            None,
        )
        assert first_display and not _INTERNAL_COL_RE.match(first_display), (
            f"metadata should expose display names, got {first_display!r}"
        )
        transformed_column = "doubled"
        if numeric is not None:
            _run(["view", "transform", "math", str(view_id),
                  "--input", json.dumps({"expression": f"{numeric} * 2",
                                         "new_column": transformed_column})], env)
            # The metadata now reflects the latest pipeline sequence, so the
            # column a transform just added is present without any extra step.
            after = _run(["view", "get", str(view_id)], env)[_DATA_KEY].get(_METADATA_KEY) or []
            names = [c.get(_DISPLAY_NAME_KEY) for c in after if isinstance(c, dict)]
            assert transformed_column in names, f"transformed column missing: {names}"
        else:
            transformed_column = None
            _run(["view", "transform", "filter", str(view_id),
                  "--input", json.dumps({"condition": {"column": first_display,
                                                       "operator": "IS_NOT_EMPTY"}})], env)

        # 6) Preview with no --input and no dataset id: default 50 rows and
        #    *every* column, by display name — never internal column_N ids,
        #    never the system hash column, and it must include the column the
        #    transform just added. The dataset is resolved from the view id.
        preview = _run(["view", "preview", str(view_id)], env)[_DATA_KEY]
        cols = preview[_COLUMNS_KEY]
        assert cols and not any(_INTERNAL_COL_RE.match(c) for c in cols), (
            f"preview leaked internal column ids: {cols}"
        )
        assert "hash" not in cols, f"preview leaked the system hash column: {cols}"
        if transformed_column is not None:
            assert transformed_column in cols, (
                f"preview missing the transformed column {transformed_column!r}: {cols}"
            )

        # 7) Export the view to a local CSV file (explicit path for cleanup).
        out = tmp_path / "quickstart_export.csv"
        _run(["view", "export", "csv", str(view_id),
              "--input", json.dumps({"output_path": str(out), "dataset_id": dataset_id})], env)
        assert out.exists() and out.stat().st_size > 0, "export did not write a non-empty CSV"
        assert out.read_text(encoding="utf-8").strip(), "exported CSV is empty"

    finally:
        if dataset_id is not None:
            make_runner().invoke(
                ["dataset", "delete", str(dataset_id), "--project", live_project,
                 "--yes", "--output", "json", "--no-input"],
                env=live_env,
            )
        if folder_id is not None:
            make_runner().invoke(
                ["folder", "delete", str(folder_id), "--project", live_project,
                 "--yes", "--output", "json", "--no-input"],
                env=live_env,
            )
