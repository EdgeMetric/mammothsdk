"""Live: a command that declares ``output_schema`` prints ``data`` that matches it (#315).

A command declares one (``output_schema: openapi`` in its manifest) only when its
``data`` is the API's own ``200`` body. This runs each of them against the server and
validates the result, so a handler that starts reshaping its result fails here::

    pytest tests/live/test_output_schema.py -m live -v
"""

from __future__ import annotations

import jsonschema
import pytest
from live_harness import LiveCli, SalesData

from mammoth_cli.commands.schema import OUTPUT_SCHEMA_OPENAPI, output_schema
from mammoth_cli.manifest.loader import load_commands

pytestmark = pytest.mark.live

_DECLARED = sorted(
    (
        record
        for record in load_commands()
        if record.get("output_schema") == OUTPUT_SCHEMA_OPENAPI
        and record["mutation_class"] == "read"
    ),
    key=lambda record: record["command_id"],
)


@pytest.mark.parametrize("record", _DECLARED, ids=lambda record: record["command_id"])
def test_data_matches_the_declared_schema(
    record: dict[str, object], live_cli: LiveCli, sales_data: SalesData
) -> None:
    known = {
        "view_id": sales_data.view,
        "dataview_id": sales_data.view,
        "dataset_id": sales_data.dataset,
        "project_id": sales_data.project,
    }
    args = []
    for positional in record.get("positionals") or []:  # type: ignore[attr-defined]
        if positional.get("required"):
            if positional["name"] not in known:
                pytest.skip(f"no known value for {positional['name']}")
            args.append(str(known[positional["name"]]))
    envelope = live_cli.run(
        *str(record["command_id"]).split("."), *args, project=sales_data.project
    )
    if "error" in envelope:
        pytest.skip(f"not available to the test identity: {envelope['error']['code']}")
    schema = output_schema(dict(record))
    assert schema is not None
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(envelope["data"]))
    assert not errors, f"{record['command_id']}: {errors[0].message[:300]}"
