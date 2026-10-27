"""Live checks: `dataset from-url` previews a link, lists linked datasets, follows or copies one.

    MAMMOTH_EVAL_TOKEN_FILE=... MAMMOTH_SERVER_PREFIX=... \\
        pytest tests/live/test_dataset_from_url.py -m live -v

The server needs mvc-service's From URL routes (#7166, #7169). ``MAMMOTH_LINK_CSV_URL`` names a
public CSV it can reach.
"""

from __future__ import annotations

import json
import os
import time

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live

CSV_URL = os.environ.get(
    "MAMMOTH_LINK_CSV_URL",
    "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
)


def _linked(cli: LiveCli, project: int) -> list[int]:
    listed, _ = cli.ok("dataset", "from-url", "links", project=project)
    return [row["id"] for row in listed["datasets"] if row["url"] == CSV_URL]


def test_preview_shows_the_columns_and_rows_of_the_file(
    live_cli: LiveCli, scratch_project: int
) -> None:
    preview, _ = live_cli.ok("dataset", "from-url", "preview", CSV_URL, project=scratch_project)
    table = preview["tables"][0]
    assert len(table["columns"]) > 1 and table["sample_rows"]


def test_follow_false_makes_a_copy_and_follow_true_links_it_again(
    live_cli: LiveCli, scratch_project: int
) -> None:
    spec = {"dataset_spec": {"url": CSV_URL}, "ds_creation_type": "weburl"}
    live_cli.ok(
        *("dataset", "create", "--input", json.dumps(spec)), "--yes", project=scratch_project
    )
    deadline = time.time() + 120
    while not _linked(live_cli, scratch_project) and time.time() < deadline:
        time.sleep(5)
    dataset = _linked(live_cli, scratch_project)[-1]

    off, _ = live_cli.ok(
        *("dataset", "from-url", "follow", str(dataset), "--input", '{"follow": false}'),
        "--yes",
        project=scratch_project,
    )
    # The server answers {"follow_link": x}; the write envelope adds "state" and "verify".
    assert off["follow_link"] is False
    assert dataset not in _linked(live_cli, scratch_project)

    on, _ = live_cli.ok(
        *("dataset", "from-url", "follow", str(dataset), "--input", '{"follow": true}'),
        "--yes",
        project=scratch_project,
    )
    assert on["follow_link"] is True
    assert dataset in _linked(live_cli, scratch_project)
