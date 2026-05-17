from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from aiokafka import AIOKafkaConsumer

from .models import LinkUpdate

logger = logging.getLogger(__name__)


class KafkaUpdateConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        on_update: Callable[[LinkUpdate], Awaitable[None]],
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._on_update = on_update
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer is not None:
            await self._consumer.stop()

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        try:
            async for msg in self._consumer:
                await self._process_message(msg.value)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception(
                "kafka_consume_error",
                extra={"event": "kafka_consume_error", "error": str(exc)},
            )

    async def _process_message(self, raw: bytes) -> None:
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("expected a JSON object")
            update = LinkUpdate.from_dict(data)
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            logger.warning(
                "kafka_deserialization_failed",
                extra={"event": "kafka_deserialization_failed", "error": str(exc)},
            )
            return

        try:
            await self._on_update(update)
            logger.info(
                "kafka_update_processed",
                extra={"event": "kafka_update_processed", "url": update.url},
            )
        except Exception as exc:
            logger.exception(
                "kafka_update_handler_failed",
                extra={"event": "kafka_update_handler_failed", "error": str(exc)},
            )
