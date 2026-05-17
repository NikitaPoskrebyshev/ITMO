from __future__ import annotations

import logging

from aiobreaker import CircuitBreakerError

from ..models.models import LinkUpdate
from .bot_client import BotClientRetryableError
from .kafka_sender import KafkaMessageSender
from .message_sender import BotHttpSender

logger = logging.getLogger(__name__)


class FallbackMessageSender:
    """Tries HTTP first; if circuit is open or all retries exhausted, uses Kafka."""

    def __init__(self, primary: BotHttpSender, fallback: KafkaMessageSender) -> None:
        self._primary = primary
        self._fallback = fallback

    async def start(self) -> None:
        await self._fallback.start()

    async def stop(self) -> None:
        await self._fallback.stop()

    async def send_update(self, update: LinkUpdate) -> None:
        try:
            await self._primary.send_update(update)
        except (CircuitBreakerError, BotClientRetryableError) as exc:
            logger.warning(
                "primary_sender_failed_fallback_to_kafka",
                extra={"error": str(exc)},
            )
            await self._fallback.send_update(update)
