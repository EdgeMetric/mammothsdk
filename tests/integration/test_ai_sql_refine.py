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
    """Asked to keep only 7 rows of the current query, the answer's SQL carries that limit."""
    generated = await client.ai.generate_sql(
        "Keep only the first 7 rows",
        dataset_id=uploaded_dataset_id,
        current_query="SELECT * FROM input_table",
    )

    assert "7" in json.dumps(generated)
