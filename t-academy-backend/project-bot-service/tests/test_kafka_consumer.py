from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from bot.kafka_consumer import KafkaUpdateConsumer
from bot.models import LinkUpdate

VALID_PAYLOAD = json.dumps(
    {
        "id": 1,
        "url": "https://github.com/x/y",
        "description": "update",
        "tgChatIds": [42],
    }
).encode()

INVALID_JSON_PAYLOAD = b"not valid json"
MISSING_FIELD_PAYLOAD = json.dumps({"id": 1, "url": "https://github.com/x/y"}).encode()
NON_OBJECT_PAYLOAD = json.dumps([1, 2, 3]).encode()


class _FakeConsumer:
    def __init__(self, messages: list[bytes]) -> None:
        self._messages = messages
        self.start = AsyncMock()
        self.stop = AsyncMock()

    def __aiter__(self):  # type: ignore[no-untyped-def]
        return self._gen()

    async def _gen(self):  # type: ignore[no-untyped-def]
        for value in self._messages:

            class _Msg:
                pass

            msg = _Msg()
            msg.value = value
            yield msg


@pytest.mark.asyncio
async def test_valid_message_calls_on_update() -> None:
    received: list[LinkUpdate] = []

    async def on_update(u: LinkUpdate) -> None:
        received.append(u)

    consumer_mock = _FakeConsumer([VALID_PAYLOAD])

    with patch("bot.kafka_consumer.AIOKafkaConsumer", return_value=consumer_mock):
        consumer = KafkaUpdateConsumer(
            bootstrap_servers="localhost:9092",
            topic="link-updates",
            group_id="test",
            on_update=on_update,
        )
        await consumer.start()
        await asyncio.sleep(0.05)
        await consumer.stop()

    assert len(received) == 1
    assert received[0].id == 1
    assert received[0].url == "https://github.com/x/y"
    assert received[0].tg_chat_ids == [42]


@pytest.mark.asyncio
async def test_invalid_json_is_skipped() -> None:
    received: list[LinkUpdate] = []

    async def on_update(u: LinkUpdate) -> None:
        received.append(u)

    consumer_mock = _FakeConsumer([INVALID_JSON_PAYLOAD])

    with patch("bot.kafka_consumer.AIOKafkaConsumer", return_value=consumer_mock):
        consumer = KafkaUpdateConsumer(
            bootstrap_servers="localhost:9092",
            topic="link-updates",
            group_id="test",
            on_update=on_update,
        )
        await consumer.start()
        await asyncio.sleep(0.05)
        await consumer.stop()

    assert len(received) == 0


@pytest.mark.asyncio
async def test_missing_field_is_skipped() -> None:
    received: list[LinkUpdate] = []

    async def on_update(u: LinkUpdate) -> None:
        received.append(u)

    consumer_mock = _FakeConsumer([MISSING_FIELD_PAYLOAD])

    with patch("bot.kafka_consumer.AIOKafkaConsumer", return_value=consumer_mock):
        consumer = KafkaUpdateConsumer(
            bootstrap_servers="localhost:9092",
            topic="link-updates",
            group_id="test",
            on_update=on_update,
        )
        await consumer.start()
        await asyncio.sleep(0.05)
        await consumer.stop()

    assert len(received) == 0


@pytest.mark.asyncio
async def test_non_object_json_is_skipped() -> None:
    received: list[LinkUpdate] = []

    async def on_update(u: LinkUpdate) -> None:
        received.append(u)

    consumer_mock = _FakeConsumer([NON_OBJECT_PAYLOAD])

    with patch("bot.kafka_consumer.AIOKafkaConsumer", return_value=consumer_mock):
        consumer = KafkaUpdateConsumer(
            bootstrap_servers="localhost:9092",
            topic="link-updates",
            group_id="test",
            on_update=on_update,
        )
        await consumer.start()
        await asyncio.sleep(0.05)
        await consumer.stop()

    assert len(received) == 0


@pytest.mark.asyncio
async def test_handler_exception_does_not_crash_consumer() -> None:
    call_count = 0

    async def on_update(u: LinkUpdate) -> None:
        nonlocal call_count
        call_count += 1
        raise RuntimeError("processing failed")

    consumer_mock = _FakeConsumer([VALID_PAYLOAD])

    with patch("bot.kafka_consumer.AIOKafkaConsumer", return_value=consumer_mock):
        consumer = KafkaUpdateConsumer(
            bootstrap_servers="localhost:9092",
            topic="link-updates",
            group_id="test",
            on_update=on_update,
        )
        await consumer.start()
        await asyncio.sleep(0.05)
        await consumer.stop()

    assert call_count == 1
