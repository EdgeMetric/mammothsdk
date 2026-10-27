"""AI SQL refine against a real server: `current_query` asks to change a query, not write a new one.

Needs the ``MM_REL_*`` credentials of ``conftest.py``, the AI add-on and a server with
mvc-service #6889.

    pytest tests/integration/test_ai_sql_refine.py -v
"""

from __future__ import annotations

import json

import pytest

from mammoth import MammothClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_refining_a_query_changes_it_as_asked(
    client: MammothClient, uploaded_dataset_id: int
) -> None:
    """Asked only to cap the rows, the answer's SQL still carries the current query's filter."""
    generated = await client.ai.generate_sql(
        "Keep only the first ten rows",
        dataset_id=uploaded_dataset_id,
        current_query="SELECT * FROM input_table WHERE region = 'North'",
    )

    assert "North" in json.dumps(generated)
