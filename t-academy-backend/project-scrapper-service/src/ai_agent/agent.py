from __future__ import annotations

import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from pydantic import ValidationError

from .config import AiAgentConfig
from .filter import UpdateFilter
from .grouper import MessageGrouper
from .models import ProcessedUpdate, RawUpdate
from .prioritizer import Prioritizer
from .summarizer import TruncatingSummarizer

logger = logging.getLogger(__name__)


class AiAgent:
    def __init__(self, config: AiAgentConfig) -> None:
        self._config = config
        self._filter = UpdateFilter(config.filtering)
        self._summarizer = TruncatingSummarizer(config.summarization, config.yandex_gpt)
        self._prioritizer = Prioritizer(config.prioritization)
        self._grouper = MessageGrouper(config.grouping.window_ms)
        self._consumer: AIOKafkaConsumer | None = None
        self._producer: AIOKafkaProducer | None = None
        self._consumer_task: asyncio.Task[None] | None = None
        self._publisher_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self._config.kafka.raw_topic,
            bootstrap_servers=self._config.kafka.bootstrap_servers,
            group_id=self._config.kafka.group_id,
            auto_offset_reset="earliest",
        )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._config.kafka.bootstrap_servers
        )
        await self._consumer.start()
        await self._producer.start()
        self._consumer_task = asyncio.create_task(self._run())
        self._publisher_task = asyncio.create_task(self._publish_loop())
        logger.info("ai_agent_started")

    async def stop(self) -> None:
        for task in (self._consumer_task, self._publisher_task):
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        if self._consumer is not None:
            await self._consumer.stop()
        if self._producer is not None:
            await self._producer.stop()
        logger.info("ai_agent_stopped")

    async def process_message(self, raw_data: bytes) -> ProcessedUpdate | None:
        try:
            data = json.loads(raw_data)
            update = RawUpdate.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("ai_agent_deserialize_failed", extra={"error": str(exc)})
            return None

        if not self._filter.should_pass(update):
            logger.info("ai_agent_filtered", extra={"id": update.id})
            return None

        description = await self._summarizer.summarize(update.description)
        priority = self._prioritizer.assign(description)
        return ProcessedUpdate(
            id=update.id,
            description=description,
            tg_chat_ids=update.tg_chat_ids,
            priority=priority,
        )

    async def _run(self) -> None:
        assert self._consumer is not None
        async for msg in self._consumer:
            try:
                processed = await self.process_message(msg.value)
                if processed is not None:
                    await self._grouper.add(processed)
            except Exception as exc:
                logger.error("ai_agent_error", extra={"error": str(exc)})

    async def _publish_loop(self) -> None:
        assert self._producer is not None
        while True:
            msg = await self._grouper.output.get()
            try:
                payload = json.dumps(msg.model_dump(by_alias=True)).encode("utf-8")
                await self._producer.send_and_wait(
                    self._config.kafka.processed_topic, payload
                )
                logger.info("ai_agent_published", extra={"id": msg.id})
            except Exception as exc:
                logger.error("ai_agent_publish_error", extra={"error": str(exc)})
