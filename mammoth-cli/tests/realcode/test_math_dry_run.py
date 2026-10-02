"""``--dry-run`` of ``view transform math`` validates the expression like a real run.

Only the HTTP socket is faked. The dry run must hit the SDK's own expression
parser (the code the real run uses) before stopping, so an expression the real
run rejects is rejected by the dry run with the identical error envelope.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.dryrun import DryRunStop, make_gate

PROJECT_ID = 180
DATASET_ID = 55
VIEW_ID = 1039
BAD_EXPRESSION = 'TRY_CAST(("tip" AS NUMERIC) * 2)'

ServiceFactory = Callable[..., Any]

_VIEW_METADATA = {
    "id": VIEW_ID,
    "name": "V",
    "metadata": [
        {"display_name": "tip", "internal_name": "column_tip", "type": "NUMERIC"},
    ],
}


def _service(real_service: ServiceFactory, *, dry_run: bool) -> Any:
    service, api = real_service(project_id=PROJECT_ID)
    api.on(
        "GET",
        rf"/resources/dataview/{VIEW_ID}$",
        body={"resource": {"object_id": VIEW_ID, "dataset": {"id": DATASET_ID, "name": "ds"}}},
    )
    api.on("GET", rf"/datasets/{DATASET_ID}/dataviews/{VIEW_ID}$", body=_VIEW_METADATA)
    api.on("POST", r"/pipeline/tasks", body={})
    api.on("GET", r"/pipeline$", body={"state": "ready"})
    if dry_run:
        service.gate = make_gate("view.transform.math")
    return service, api


def _math(service: Any, expression: str) -> None:
    service.call_view(VIEW_ID, "math", expression=expression, new_column="out")


def test_dry_run_rejects_an_expression_the_real_run_rejects(real_service: ServiceFactory) -> None:
    real, _ = _service(real_service, dry_run=False)
    with pytest.raises(CliError) as real_error:
        _math(real, BAD_EXPRESSION)
    dry, api = _service(real_service, dry_run=True)
    with pytest.raises(CliError) as dry_error:
        _math(dry, BAD_EXPRESSION)
    assert dry_error.value.code == real_error.value.code == "unknown_column"
    assert dry_error.value.details == real_error.value.details
    assert not [r for r in api.requests if r.method == "POST"]


def test_dry_run_of_a_valid_expression_still_stops_without_a_request(
    real_service: ServiceFactory,
) -> None:
    dry, api = _service(real_service, dry_run=True)
    with pytest.raises(DryRunStop) as stop:
        _math(dry, '"tip" * 2')
    assert stop.value.record["would_call"]["arguments"]["expression"] == '"tip" * 2'
    assert not [r for r in api.requests if r.method == "POST"]
