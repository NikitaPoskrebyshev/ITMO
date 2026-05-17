from __future__ import annotations

import asyncio
import json

import pytest
from aiokafka import AIOKafkaProducer

from bot.kafka_consumer import KafkaUpdateConsumer
from bot.models import LinkUpdate

TOPIC = "link-updates-integration"


@pytest.mark.asyncio
async def test_scrapper_to_bot_full_path(kafka_bootstrap_server: str) -> None:
    received: asyncio.Queue[LinkUpdate] = asyncio.Queue()

    async def on_update(update: LinkUpdate) -> None:
        await received.put(update)

    consumer = KafkaUpdateConsumer(
        bootstrap_servers=kafka_bootstrap_server,
        topic=TOPIC,
        group_id="integration-test-group",
        on_update=on_update,
    )
    await consumer.start()
    await asyncio.sleep(2)

    producer = AIOKafkaProducer(bootstrap_servers=kafka_bootstrap_server)
    await producer.start()
    try:
        payload = json.dumps(
            {
                "id": 42,
                "url": "https://github.com/octocat/Hello-World",
                "description": "New issue opened",
                "tgChatIds": [100, 200],
            }
        ).encode()
        await producer.send_and_wait(TOPIC, payload)
    finally:
        await producer.stop()

    update = await asyncio.wait_for(received.get(), timeout=15)
    await consumer.stop()

    assert update.id == 42
    assert update.url == "https://github.com/octocat/Hello-World"
    assert update.description == "New issue opened"
    assert update.tg_chat_ids == [100, 200]


@pytest.mark.asyncio
async def test_invalid_message_is_skipped(kafka_bootstrap_server: str) -> None:
    processed: list[LinkUpdate] = []

    async def on_update(update: LinkUpdate) -> None:
        processed.append(update)

    consumer = KafkaUpdateConsumer(
        bootstrap_servers=kafka_bootstrap_server,
        topic=TOPIC + "-invalid-test",
        group_id="integration-invalid-group",
        on_update=on_update,
    )
    await consumer.start()
    await asyncio.sleep(2)

    producer = AIOKafkaProducer(bootstrap_servers=kafka_bootstrap_server)
    await producer.start()
    try:
        await producer.send_and_wait(TOPIC + "-invalid-test", b"this is not json {{{")
    finally:
        await producer.stop()

    await asyncio.sleep(3)
    await consumer.stop()

    assert len(processed) == 0


@pytest.mark.asyncio
async def test_multiple_messages_all_processed(kafka_bootstrap_server: str) -> None:
    received: asyncio.Queue[LinkUpdate] = asyncio.Queue()

    async def on_update(update: LinkUpdate) -> None:
        await received.put(update)

    consumer = KafkaUpdateConsumer(
        bootstrap_servers=kafka_bootstrap_server,
        topic=TOPIC + "-multi",
        group_id="integration-multi-group",
        on_update=on_update,
    )
    await consumer.start()
    await asyncio.sleep(2)

    producer = AIOKafkaProducer(bootstrap_servers=kafka_bootstrap_server)
    await producer.start()
    try:
        for i in range(3):
            payload = json.dumps(
                {
                    "id": i,
                    "url": f"https://github.com/user/repo-{i}",
                    "description": f"Update {i}",
                    "tgChatIds": [i * 10],
                }
            ).encode()
            await producer.send_and_wait(TOPIC + "-multi", payload)
    finally:
        await producer.stop()

    updates = []
    for _ in range(3):
        u = await asyncio.wait_for(received.get(), timeout=15)
        updates.append(u)

    await consumer.stop()

    urls = {u.url for u in updates}
    assert urls == {
        "https://github.com/user/repo-0",
        "https://github.com/user/repo-1",
        "https://github.com/user/repo-2",
    }
