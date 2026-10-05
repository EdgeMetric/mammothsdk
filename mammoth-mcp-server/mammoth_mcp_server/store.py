"""The short-lived records this server keeps: sign-ins, tokens and upload tickets.

Each is one Redis key that expires by itself, so no worker keeps anything in
memory and any worker can serve any request. A record that holds a credential
holds it sealed (`seal`), so a reader of Redis learns nothing.
"""

import json
import typing

import redis.asyncio as aioredis
from cryptography.fernet import Fernet

from .config import ENCRYPTION_KEY, REDIS_URL, STORE_PREFIX

type Record = dict[str, typing.Any]

_redis: aioredis.Redis | None = None


def connect() -> aioredis.Redis:
    """The Redis client, made on first use and kept for the process."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def use(client: aioredis.Redis | None) -> None:
    """Keep records in `client` instead — a test's own store, say."""
    global _redis
    _redis = client


def cipher() -> Fernet:
    """The cipher credentials are sealed with.

    Raises:
        RuntimeError: If the deployment set no key. Credentials are never
            stored in the clear, so there is nothing to fall back to.
    """
    if not ENCRYPTION_KEY:
        raise RuntimeError("MCP_ENCRYPTION_KEY is not set")
    return Fernet(ENCRYPTION_KEY.encode())


def redis_key(kind: str, key: str) -> str:
    """Namespace one record, per deployment and per kind."""
    return f"{STORE_PREFIX}:{kind}:{key}"


def seal(credentials: Record) -> str:
    """Encrypt the caller's credentials for storage."""
    return cipher().encrypt(json.dumps(credentials).encode()).decode()


def unseal(sealed: str) -> Record:
    """Read back what `seal` stored."""
    return typing.cast(Record, json.loads(cipher().decrypt(sealed.encode())))


async def remember(kind: str, key: str, record: Record, seconds: int) -> None:
    """Store one record until it expires."""
    await connect().set(redis_key(kind, key), json.dumps(record), ex=seconds)


async def replace(kind: str, key: str, record: Record) -> None:
    """Change a record and leave it the time it had left."""
    await connect().set(redis_key(kind, key), json.dumps(record), keepttl=True)


async def recall(kind: str, key: str) -> Record | None:
    """Read one record back, or None once it is gone."""
    stored = await connect().get(redis_key(kind, key))
    return typing.cast(Record, json.loads(stored)) if stored else None


async def forget(kind: str, key: str) -> None:
    """Drop one record."""
    await connect().delete(redis_key(kind, key))
