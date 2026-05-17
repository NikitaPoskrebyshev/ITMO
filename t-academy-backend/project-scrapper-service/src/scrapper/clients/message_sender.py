from __future__ import annotations

import logging
from datetime import timedelta
from typing import Protocol, runtime_checkable

from aiobreaker import CircuitBreaker
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from ..config.config import ResilienceConfig, RetryConfig
from ..models.models import LinkUpdate
from .bot_client import BotClient, BotClientRetryableError

logger = logging.getLogger(__name__)


def _build_wait(retry: RetryConfig):
    if retry.backoff_strategy == "exponential":
        return wait_exponential(
            multiplier=retry.backoff_multiplier,
            min=retry.backoff_seconds,
            max=retry.max_backoff_seconds,
        )
    return wait_fixed(retry.backoff_seconds)


@runtime_checkable
class MessageSender(Protocol):
    async def send_update(self, update: LinkUpdate) -> None: ...


class BotHttpSender:
    def __init__(self, bot_client: BotClient, resilience: ResilienceConfig) -> None:
        self._client = bot_client
        self._retry = resilience.retry
        self._cb = CircuitBreaker(
            fail_max=resilience.circuit_breaker.fail_max,
            timeout_duration=timedelta(
                seconds=resilience.circuit_breaker.reset_timeout_seconds
            ),
            name="bot-http-sender",
        )

    async def send_update(self, update: LinkUpdate) -> None:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._retry.max_attempts),
            wait=_build_wait(self._retry),
            retry=retry_if_exception_type(BotClientRetryableError),
            reraise=True,
        ):
            with attempt:
                await self._cb.call_async(self._client.send_update, update)
