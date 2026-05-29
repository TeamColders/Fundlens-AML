from redis import asyncio as redis

from backend.core.config import settings

_client = None


def connect():
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def close() -> None:
    global _client
    if _client is not None:
        await _client.close()
        await _client.connection_pool.disconnect()
        _client = None


def get_client():
    return connect()
