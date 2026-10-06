"""The records the server keeps, and the credentials sealed inside them."""

from typing import Any
from unittest.mock import patch

import pytest

from mammoth_mcp_server import store

from .helpers import FakeRedis, a_fake_store, run


@pytest.fixture
def redis() -> Any:
    with a_fake_store() as fake:
        yield fake


class TestTheStore:
    def test_a_record_comes_back_until_it_is_dropped(self, redis: FakeRedis) -> None:
        run(store.remember("token", "abc", {"client_id": "c"}, 60))

        assert run(store.recall("token", "abc")) == {"client_id": "c"}
        run(store.forget("token", "abc"))
        assert run(store.recall("token", "abc")) is None

    def test_a_record_is_given_the_time_it_was_asked_to_live(self, redis: FakeRedis) -> None:
        run(store.remember("code", "abc", {}, 300))

        assert redis.seconds[store.redis_key("code", "abc")] == 300

    def test_two_kinds_of_record_do_not_share_a_key(self, redis: FakeRedis) -> None:
        run(store.remember("code", "abc", {"kind": "code"}, 60))

        assert run(store.recall("token", "abc")) is None

    def test_sealed_credentials_are_not_readable_in_the_store(self, redis: FakeRedis) -> None:
        sealed = store.seal({"api_token": "mm_secret"})

        assert "mm_secret" not in sealed
        assert store.unseal(sealed) == {"api_token": "mm_secret"}

    def test_nothing_is_sealed_without_a_key(self) -> None:
        # Credentials are never stored in the clear, so there is no fallback.
        with (
            patch.object(store, "ENCRYPTION_KEY", ""),
            pytest.raises(RuntimeError, match="MCP_ENCRYPTION_KEY"),
        ):
            store.seal({"api_token": "mm_secret"})
