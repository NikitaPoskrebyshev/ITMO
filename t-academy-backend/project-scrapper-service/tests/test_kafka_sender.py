from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from scrapper.clients.kafka_sender import KafkaMessageSender
from scrapper.models.models import LinkUpdate

UPDATE = LinkUpdate(
    id=1, url="https://github.com/x/y", description="test update", tg_chat_ids=[42, 99]
)


def _make_producer_mock() -> AsyncMock:
    producer = AsyncMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    producer.send_and_wait = AsyncMock()
    return producer


async def test_kafka_sender_sends_message_to_correct_topic() -> None:
    mock = _make_producer_mock()
    with patch("scrapper.clients.kafka_sender.AIOKafkaProducer", return_value=mock):
        sender = KafkaMessageSender(
            bootstrap_servers="localhost:9092", topic="link-updates"
        )
        await sender.start()
        await sender.send_update(UPDATE)
        await sender.stop()

    mock.send_and_wait.assert_called_once()
    topic_arg = mock.send_and_wait.call_args[0][0]
    assert topic_arg == "link-updates"


async def test_kafka_sender_serializes_to_json_with_alias() -> None:
    mock = _make_producer_mock()
    with patch("scrapper.clients.kafka_sender.AIOKafkaProducer", return_value=mock):
        sender = KafkaMessageSender(
            bootstrap_servers="localhost:9092", topic="link-updates"
        )
        await sender.start()
        await sender.send_update(UPDATE)

    payload_bytes = mock.send_and_wait.call_args[0][1]
    data = json.loads(payload_bytes)
    assert data["id"] == 1
    assert data["url"] == "https://github.com/x/y"
    assert data["description"] == "test update"
    assert data["tgChatIds"] == [42, 99]


async def test_kafka_sender_starts_and_stops_producer() -> None:
    mock = _make_producer_mock()
    with patch("scrapper.clients.kafka_sender.AIOKafkaProducer", return_value=mock):
        sender = KafkaMessageSender(
            bootstrap_servers="localhost:9092", topic="link-updates"
        )
        await sender.start()
        await sender.stop()

    mock.start.assert_called_once()
    mock.stop.assert_called_once()


async def test_kafka_sender_not_started_raises() -> None:
    sender = KafkaMessageSender(
        bootstrap_servers="localhost:9092", topic="link-updates"
    )
    with pytest.raises(RuntimeError, match="not started"):
        await sender.send_update(UPDATE)


async def test_kafka_sender_send_error_does_not_raise() -> None:
    mock = _make_producer_mock()
    mock.send_and_wait.side_effect = Exception("broker unavailable")
    with patch("scrapper.clients.kafka_sender.AIOKafkaProducer", return_value=mock):
        sender = KafkaMessageSender(
            bootstrap_servers="localhost:9092", topic="link-updates"
        )
        await sender.start()
        await sender.send_update(UPDATE)  # should not raise


async def test_app_uses_fallback_sender_when_transport_is_http(mocker) -> None:
    from scrapper.app import create_app
    from scrapper.clients.fallback_sender import FallbackMessageSender
    from scrapper.config.config import AppConfig
    from scrapper.scheduler.scheduler import Scheduler

    mocker.patch.object(Scheduler, "start")
    mocker.patch.object(Scheduler, "stop")
    mocker.patch(
        "scrapper.clients.kafka_sender.AIOKafkaProducer",
        return_value=_make_producer_mock(),
    )

    captured: dict = {}
    original_init = Scheduler.__init__

    def capture_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        captured["sender"] = kwargs.get("sender")
        original_init(self, *args, **kwargs)

    mocker.patch.object(Scheduler, "__init__", capture_init)

    config = AppConfig()
    app = create_app(config)

    async with app.router.lifespan_context(app):
        pass

    assert isinstance(captured.get("sender"), FallbackMessageSender)


async def test_app_uses_kafka_sender_when_transport_is_kafka(mocker) -> None:
    from scrapper.app import create_app
    from scrapper.clients.kafka_sender import KafkaMessageSender
    from scrapper.config.config import (
        AppConfig,
        KafkaProducerConfig,
        NotificationConfig,
    )
    from scrapper.scheduler.scheduler import Scheduler

    mocker.patch.object(Scheduler, "start")
    mocker.patch.object(Scheduler, "stop")
    mocker.patch(
        "scrapper.clients.kafka_sender.AIOKafkaProducer",
        return_value=_make_producer_mock(),
    )

    captured: dict = {}
    original_init = Scheduler.__init__

    def capture_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        captured["sender"] = kwargs.get("sender")
        original_init(self, *args, **kwargs)

    mocker.patch.object(Scheduler, "__init__", capture_init)

    config = AppConfig(
        notification=NotificationConfig(
            transport="kafka",
            kafka=KafkaProducerConfig(
                bootstrap_servers="localhost:9092", topic="link-updates"
            ),
        )
    )
    app = create_app(config)

    async with app.router.lifespan_context(app):
        pass

    assert isinstance(captured.get("sender"), KafkaMessageSender)
