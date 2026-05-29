import asyncio
from typing import AsyncIterator

from backend.core.config import settings
from backend.db.redis_client import get_client


async def subscribe_alerts() -> AsyncIterator[str]:
    client = get_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(settings.alerts_channel)
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("data"):
                yield message["data"]
            await asyncio.sleep(0.05)
    finally:
        await pubsub.unsubscribe(settings.alerts_channel)
        await pubsub.close()


async def publish_alert(payload: str) -> None:
    client = get_client()
    await client.publish(settings.alerts_channel, payload)
