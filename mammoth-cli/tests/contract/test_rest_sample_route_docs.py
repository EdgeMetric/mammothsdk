"""`connector connection query` refuses a REST config.

Changelog analytics build, 2026-10-15: the command runs one read-only SQL
SELECT and refuses anything else before a request is sent
(`commands/connector.py` `_require_read_only_sql`). The route that works for a
REST sample is `connector ds-config create ... {"data_sample": true}`.
"""

import pytest

from mammoth_cli.commands.connector import _require_read_only_sql

_REST_QUERY = '{"endpoint_path": "/posts", "data_root_path": "$", "max_pages": 1}'


def test_connection_query_refuses_a_rest_config() -> None:
    """The premise: if this ever accepts a REST config, the docs can say so again."""
    with pytest.raises(Exception):
        _require_read_only_sql(_REST_QUERY)
