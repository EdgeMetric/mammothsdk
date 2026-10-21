"""SDK side of the PRD-3119 prod-log follow-ups, against a real loopback HTTP server."""

from __future__ import annotations

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError
from tests.unit._loopback import RecordingServer, client, server  # noqa: F401

BATCH_DATA = "/workspaces/1/projects/25654/datasets/275350/batches/9/data"


async def test_batch_data_sends_a_column_list_as_one_comma_separated_string(
    client: MammothClient, server: RecordingServer  # noqa: F811
) -> None:
    await client.datasets.get_batch_data(275350, 9, columns=["column_1", "column_2"])

    assert server.requests[0]["path"] == BATCH_DATA
    assert server.requests[0]["query"]["columns"] == "column_1,column_2"  # type: ignore[index]


async def test_batch_data_still_sends_a_string_as_given(
    client: MammothClient, server: RecordingServer  # noqa: F811
) -> None:
    await client.datasets.get_batch_data(275350, 9, columns="column_1")

    assert server.requests[0]["query"]["columns"] == "column_1"  # type: ignore[index]


@pytest.mark.parametrize(
    ("kwargs", "words"),
    [
        ({}, "table_list"),
        ({"table_list": [0], "is_preview_needed": True}, "not both"),
        ({"table_list": [0], "user_instruction": "x"}, "user_instruction"),
    ],
)
async def test_create_from_pdf_refuses_what_the_api_refuses_before_any_request(
    client: MammothClient,  # noqa: F811
    server: RecordingServer,  # noqa: F811
    kwargs: dict[str, object],
    words: str,
) -> None:
    with pytest.raises(MammothValidationError, match=words):
        await client.datasets.create_from_pdf(5, "report.pdf", **kwargs)  # type: ignore[arg-type]

    assert server.requests == []


async def test_create_from_pdf_sends_a_preview_request(
    client: MammothClient, server: RecordingServer  # noqa: F811
) -> None:
    await client.datasets.create_from_pdf(5, "report.pdf", is_preview_needed=True)

    body = server.requests[0]["body"]
    assert isinstance(body, dict)
    assert body["is_preview_needed"] is True and "table_list" not in body
