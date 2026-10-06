"""parse_post_response keeps the one-time token and says so when the model drifts.

Pure model parsing of a dict (no network, no doubles).
"""

from __future__ import annotations

import warnings

import pytest

from mammoth.api.clientapps import parse_post_response
from mammoth.exceptions import MammothModelDriftWarning

LIVE_SHAPE = {
    "app_name": "n",
    "app_key": "k",
    "description": "",
    "workspace_id": 4,
    "user_id": 5,
    "token": "mm_secret-token",
}


def test_matching_response_parses_without_a_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert parse_post_response(LIVE_SHAPE).token == "mm_secret-token"


def test_drifted_response_still_returns_the_token_and_warns_with_field_names() -> None:
    with pytest.warns(MammothModelDriftWarning) as caught:
        parsed = parse_post_response({**LIVE_SHAPE, "workspace_id": "four", "user_id": None})
    assert parsed.token == "mm_secret-token"
    message = str(caught[0].message)
    assert "workspace_id" in message and "user_id" in message
    assert "mm_secret-token" not in message
