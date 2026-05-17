from __future__ import annotations

import asyncio
import json

import pytest

from ai_agent.config import (
    AiAgentConfig,
    AiAgentKafkaConfig,
    FilteringConfig,
    SummarizationConfig,
)
from ai_agent.filter import UpdateFilter
from ai_agent.models import RawUpdate
from ai_agent.summarizer import TruncatingSummarizer


def _make_update(description: str, author: str = "user") -> RawUpdate:
    return RawUpdate.model_validate(
        {"id": 1, "description": description, "author": author, "tgChatIds": [42]}
    )


def test_filter_stop_word_blocks_update() -> None:
    f = UpdateFilter(FilteringConfig(stop_words=("spam",)))
    assert not f.should_pass(_make_update("this is spam content"))


def test_filter_stop_word_case_insensitive() -> None:
    f = UpdateFilter(FilteringConfig(stop_words=("spam",)))
    assert not f.should_pass(_make_update("Contains SPAM here"))


def test_filter_excluded_author_blocks_update() -> None:
    f = UpdateFilter(FilteringConfig(excluded_authors=("bot-user",)))
    assert not f.should_pass(_make_update("normal content", author="bot-user"))


def test_filter_min_length_blocks_short_update() -> None:
    f = UpdateFilter(FilteringConfig(min_length=20))
    assert not f.should_pass(_make_update("short"))


def test_filter_valid_update_passes() -> None:
    f = UpdateFilter(
        FilteringConfig(
            stop_words=("spam",),
            excluded_authors=("bot-user",),
            min_length=5,
        )
    )
    assert f.should_pass(_make_update("valid content here", author="developer"))


def test_filter_no_config_passes_everything() -> None:
    f = UpdateFilter(FilteringConfig())
    assert f.should_pass(_make_update(""))


async def test_summarizer_truncates_long_text() -> None:
    s = TruncatingSummarizer(SummarizationConfig(threshold=10))
    result = await s.summarize("a" * 30)
    assert result == "a" * 10 + "..."
    assert len(result) == 13


async def test_summarizer_leaves_short_text_unchanged() -> None:
    s = TruncatingSummarizer(SummarizationConfig(threshold=100))
    text = "short text"
    assert await s.summarize(text) == text


async def test_summarizer_exact_threshold_not_truncated() -> None:
    s = TruncatingSummarizer(SummarizationConfig(threshold=5))
    assert await s.summarize("hello") == "hello"


@pytest.fixture(scope="session")
def kafka_bootstrap() -> str:
    from testcontainers.kafka import KafkaContainer

    with KafkaContainer() as kafka:
        yield kafka.get_bootstrap_server()


async def test_receive_and_process_valid_message(kafka_bootstrap: str) -> None:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

    from ai_agent.agent import AiAgent

    config = AiAgentConfig(
        filtering=FilteringConfig(min_length=1),
        summarization=SummarizationConfig(threshold=500),
        kafka=AiAgentKafkaConfig(
            bootstrap_servers=kafka_bootstrap,
            raw_topic="tc11.raw",
            processed_topic="tc11.processed",
            group_id="tc11-agent",
        ),
    )
    agent = AiAgent(config)
    await agent.start()

    try:
        producer = AIOKafkaProducer(bootstrap_servers=kafka_bootstrap)
        await producer.start()
        msg = {
            "id": 99,
            "description": "important update about the repository",
            "author": "developer",
            "tgChatIds": [111, 222],
        }
        await producer.send_and_wait("tc11.raw", json.dumps(msg).encode())
        await producer.stop()

        consumer = AIOKafkaConsumer(
            "tc11.processed",
            bootstrap_servers=kafka_bootstrap,
            group_id="tc11-verify",
            auto_offset_reset="earliest",
        )
        await consumer.start()
        try:
            received = await asyncio.wait_for(consumer.__anext__(), timeout=15.0)
            data = json.loads(received.value)
            assert data["id"] == 99
            assert "tgChatIds" in data
            assert data["tgChatIds"] == [111, 222]
        finally:
            await consumer.stop()
    finally:
        await agent.stop()


async def test_invalid_message_does_not_crash_agent(kafka_bootstrap: str) -> None:
    from aiokafka import AIOKafkaProducer

    from ai_agent.agent import AiAgent

    config = AiAgentConfig(
        kafka=AiAgentKafkaConfig(
            bootstrap_servers=kafka_bootstrap,
            raw_topic="tc12.raw",
            processed_topic="tc12.processed",
            group_id="tc12-agent",
        ),
    )
    agent = AiAgent(config)
    await agent.start()

    try:
        producer = AIOKafkaProducer(bootstrap_servers=kafka_bootstrap)
        await producer.start()
        await producer.send_and_wait("tc12.raw", b"{ not valid json }{{{")
        await producer.stop()

        await asyncio.sleep(3.0)

        assert agent._task is not None
        assert not agent._task.done()
    finally:
        await agent.stop()
