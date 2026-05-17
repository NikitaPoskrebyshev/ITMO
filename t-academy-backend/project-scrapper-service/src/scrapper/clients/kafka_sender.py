from __future__ import annotations

import json
import logging

from aiokafka import AIOKafkaProducer

from ..models.models import LinkUpdate

logger = logging.getLogger(__name__)


class KafkaMessageSender:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def send_update(self, update: LinkUpdate) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaMessageSender is not started")
        payload = json.dumps(update.model_dump(by_alias=True)).encode("utf-8")
        try:
            await self._producer.send_and_wait(self._topic, payload)
            logger.info(
                "kafka_send_update",
                extra={"event": "kafka_send_update", "url": update.url},
            )
        except Exception as exc:
            logger.error(
                "kafka_send_failed",
                extra={"event": "kafka_send_failed", "error": str(exc)},
            )
