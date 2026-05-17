from __future__ import annotations

import asyncio
import time
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from scrapper.app import create_app
from scrapper.clients.bot_client import (
    BotClient,
    BotClientNonRetryableError,
    BotClientRetryableError,
)
from scrapper.clients.fallback_sender import FallbackMessageSender
from scrapper.clients.message_sender import BotHttpSender
from scrapper.config.config import (
    AppConfig,
    CircuitBreakerConfig,
    RateLimitConfig,
    ResilienceConfig,
    RetryConfig,
)
from scrapper.models.models import LinkUpdate

UPDATE = LinkUpdate(
    id=1, url="https://github.com/x/y", description="test", tg_chat_ids=[42]
)


def _http_mock(status_code: int):
    resp = MagicMock()
    resp.status_code = status_code
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(
        return_value=MagicMock(post=AsyncMock(return_value=resp))
    )
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


def _make_bot_client(
    status_codes: list[int], retryable: tuple[int, ...] = (500, 502, 503, 504)
) -> tuple[BotClient, list]:
    calls: list[int] = []

    async def fake_post(*args, **kwargs):
        code = status_codes[len(calls)]
        calls.append(code)
        resp = MagicMock()
        resp.status_code = code
        return resp

    client = BotClient(
        base_url="http://bot", timeout_seconds=1, retryable_status_codes=retryable
    )
    return client, calls


# Timeout


async def test_timeout_raises_retryable_error(mocker) -> None:  # type: ignore[no-untyped-def]
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)
    mock.post.side_effect = httpx.TimeoutException("timed out")
    mocker.patch("scrapper.clients.bot_client.httpx.AsyncClient", return_value=mock)

    client = BotClient(base_url="http://bot", timeout_seconds=1)
    with pytest.raises(BotClientRetryableError, match="timeout"):
        await client.send_update(UPDATE)


# Retry


async def test_retry_on_5xx_succeeds_after_failures(mocker) -> None:  # type: ignore[no-untyped-def]
    statuses = [500, 500, 200]
    call_count = 0

    async def fake_send(update: LinkUpdate) -> None:
        nonlocal call_count
        code = statuses[call_count]
        call_count += 1
        if code != 200:
            raise BotClientRetryableError(f"HTTP {code}")

    resilience = ResilienceConfig(
        retry=RetryConfig(max_attempts=3, backoff_seconds=0.01),
    )
    sender = BotHttpSender.__new__(BotHttpSender)
    sender._retry = resilience.retry
    from aiobreaker import CircuitBreaker

    sender._cb = CircuitBreaker(fail_max=10, timeout_duration=timedelta(seconds=60))
    sender._client = MagicMock()
    sender._client.send_update = fake_send

    await sender.send_update(UPDATE)
    assert call_count == 3


async def test_no_retry_on_4xx(mocker) -> None:  # type: ignore[no-untyped-def]
    call_count = 0

    async def fake_send(update: LinkUpdate) -> None:
        nonlocal call_count
        call_count += 1
        raise BotClientNonRetryableError("HTTP 400")

    resilience = ResilienceConfig(
        retry=RetryConfig(max_attempts=3, backoff_seconds=0.01),
    )
    sender = BotHttpSender.__new__(BotHttpSender)
    sender._retry = resilience.retry
    from aiobreaker import CircuitBreaker

    sender._cb = CircuitBreaker(fail_max=10, timeout_duration=timedelta(seconds=60))
    sender._client = MagicMock()
    sender._client.send_update = fake_send

    with pytest.raises(BotClientNonRetryableError):
        await sender.send_update(UPDATE)
    assert call_count == 1


async def test_retry_constant_backoff_delay() -> None:
    call_count = 0
    timestamps: list[float] = []

    async def fake_send(update: LinkUpdate) -> None:
        nonlocal call_count
        timestamps.append(time.monotonic())
        call_count += 1
        if call_count < 3:
            raise BotClientRetryableError("HTTP 500")

    backoff = 0.05
    resilience = ResilienceConfig(
        retry=RetryConfig(max_attempts=3, backoff_seconds=backoff),
    )
    sender = BotHttpSender.__new__(BotHttpSender)
    sender._retry = resilience.retry
    from aiobreaker import CircuitBreaker

    sender._cb = CircuitBreaker(fail_max=10, timeout_duration=timedelta(seconds=60))
    sender._client = MagicMock()
    sender._client.send_update = fake_send

    await sender.send_update(UPDATE)

    assert len(timestamps) == 3
    assert timestamps[1] - timestamps[0] >= backoff * 0.8
    assert timestamps[2] - timestamps[1] >= backoff * 0.8


# Rate Limiting


@pytest.fixture
def rate_limited_app(mocker):  # type: ignore[no-untyped-def]
    mocker.patch("scrapper.scheduler.scheduler.Scheduler.start")
    mocker.patch("scrapper.scheduler.scheduler.Scheduler.stop")
    config = AppConfig(
        resilience=ResilienceConfig(rate_limit=RateLimitConfig(requests_per_minute=3))
    )
    return create_app(config)


@pytest_asyncio.fixture
async def rate_limited_client(rate_limited_app) -> AsyncClient:  # type: ignore[misc]
    async with AsyncClient(
        transport=ASGITransport(app=rate_limited_app), base_url="http://test"
    ) as c:
        yield c


async def test_rate_limit_returns_429_when_exceeded(
    rate_limited_client: AsyncClient,
) -> None:
    await rate_limited_client.post("/tg-chat/1")
    responses = [
        await rate_limited_client.get("/links", headers={"Tg-Chat-Id": "1"})
        for _ in range(5)
    ]
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes


async def test_rate_limit_allows_requests_within_limit(
    rate_limited_client: AsyncClient,
) -> None:
    await rate_limited_client.post("/tg-chat/2")
    responses = [
        await rate_limited_client.get("/links", headers={"Tg-Chat-Id": "2"})
        for _ in range(2)
    ]
    assert all(r.status_code == 200 for r in responses)


# Circuit Breaker


def _make_sender_with_cb(
    fail_max: int = 3, reset_timeout: float = 0.1
) -> BotHttpSender:
    resilience = ResilienceConfig(
        retry=RetryConfig(max_attempts=1, backoff_seconds=0.01),
        circuit_breaker=CircuitBreakerConfig(
            fail_max=fail_max, reset_timeout_seconds=1
        ),
    )
    client = BotClient(base_url="http://bot", timeout_seconds=1)
    sender = BotHttpSender(client, resilience)
    from aiobreaker import CircuitBreaker

    sender._cb = CircuitBreaker(
        fail_max=fail_max, timeout_duration=timedelta(seconds=reset_timeout)
    )
    return sender


async def test_circuit_breaker_opens_after_failures() -> None:
    from aiobreaker import CircuitBreakerError

    sender = _make_sender_with_cb(fail_max=3)
    call_count = 0

    async def always_fail(update: LinkUpdate) -> None:
        nonlocal call_count
        call_count += 1
        raise BotClientRetryableError("HTTP 500")

    sender._client.send_update = always_fail

    for _ in range(3):
        with pytest.raises((BotClientRetryableError, CircuitBreakerError)):
            await sender.send_update(UPDATE)

    call_count_before_open = call_count

    with pytest.raises(CircuitBreakerError):
        await sender.send_update(UPDATE)

    assert call_count == call_count_before_open


async def test_circuit_breaker_half_open_to_closed() -> None:
    from aiobreaker import CircuitBreakerError

    sender = _make_sender_with_cb(fail_max=2, reset_timeout=0.1)
    call_count = 0
    should_fail = True

    async def conditional_fail(update: LinkUpdate) -> None:
        nonlocal call_count
        call_count += 1
        if should_fail:
            raise BotClientRetryableError("HTTP 500")

    sender._client.send_update = conditional_fail

    for _ in range(2):
        with pytest.raises((BotClientRetryableError, CircuitBreakerError)):
            await sender.send_update(UPDATE)

    await asyncio.sleep(0.15)

    should_fail = False
    await sender.send_update(UPDATE)

    await sender.send_update(UPDATE)


async def test_circuit_breaker_half_open_to_open_on_failure() -> None:
    from aiobreaker import CircuitBreakerError

    sender = _make_sender_with_cb(fail_max=2, reset_timeout=0.1)

    async def always_fail(update: LinkUpdate) -> None:
        raise BotClientRetryableError("HTTP 500")

    sender._client.send_update = always_fail

    for _ in range(2):
        with pytest.raises((BotClientRetryableError, CircuitBreakerError)):
            await sender.send_update(UPDATE)

    await asyncio.sleep(0.15)

    with pytest.raises((BotClientRetryableError, CircuitBreakerError)):
        await sender.send_update(UPDATE)

    with pytest.raises(CircuitBreakerError):
        await sender.send_update(UPDATE)


# Fallback


async def test_fallback_uses_kafka_when_http_circuit_open() -> None:
    from datetime import datetime

    from aiobreaker import CircuitBreakerError

    primary = AsyncMock(spec=BotHttpSender)
    primary.send_update.side_effect = CircuitBreakerError(
        "circuit open", datetime.now() + timedelta(seconds=60)
    )

    kafka_fallback = AsyncMock()
    kafka_fallback.send_update = AsyncMock()

    sender = FallbackMessageSender(primary, kafka_fallback)
    await sender.send_update(UPDATE)

    primary.send_update.assert_called_once_with(UPDATE)
    kafka_fallback.send_update.assert_called_once_with(UPDATE)


async def test_fallback_uses_kafka_when_retries_exhausted() -> None:
    primary = AsyncMock(spec=BotHttpSender)
    primary.send_update.side_effect = BotClientRetryableError("all retries exhausted")

    kafka_fallback = AsyncMock()
    kafka_fallback.send_update = AsyncMock()

    sender = FallbackMessageSender(primary, kafka_fallback)
    await sender.send_update(UPDATE)

    kafka_fallback.send_update.assert_called_once_with(UPDATE)


async def test_fallback_does_not_use_kafka_on_success() -> None:
    primary = AsyncMock(spec=BotHttpSender)
    primary.send_update = AsyncMock()

    kafka_fallback = AsyncMock()
    kafka_fallback.send_update = AsyncMock()

    sender = FallbackMessageSender(primary, kafka_fallback)
    await sender.send_update(UPDATE)

    kafka_fallback.send_update.assert_not_called()


# Bonus: Exponential backoff


async def test_exponential_backoff_delay_grows() -> None:
    call_count = 0
    timestamps: list[float] = []

    async def fake_send(update: LinkUpdate) -> None:
        nonlocal call_count
        timestamps.append(time.monotonic())
        call_count += 1
        if call_count < 4:
            raise BotClientRetryableError("HTTP 500")

    base = 0.05
    resilience = ResilienceConfig(
        retry=RetryConfig(
            max_attempts=4,
            backoff_seconds=base,
            backoff_strategy="exponential",
            backoff_multiplier=2.0,
            max_backoff_seconds=10.0,
        ),
    )
    sender = BotHttpSender.__new__(BotHttpSender)
    sender._retry = resilience.retry
    from aiobreaker import CircuitBreaker

    sender._cb = CircuitBreaker(fail_max=10, timeout_duration=timedelta(seconds=60))
    sender._client = MagicMock()
    sender._client.send_update = fake_send

    await sender.send_update(UPDATE)

    assert len(timestamps) == 4
    gap1 = timestamps[1] - timestamps[0]
    gap2 = timestamps[2] - timestamps[1]
    gap3 = timestamps[3] - timestamps[2]
    assert gap2 >= gap1 * 1.5
    assert gap3 >= gap2 * 1.5


async def test_exponential_backoff_capped_at_max() -> None:
    call_count = 0
    timestamps: list[float] = []

    async def fake_send(update: LinkUpdate) -> None:
        nonlocal call_count
        timestamps.append(time.monotonic())
        call_count += 1
        if call_count < 4:
            raise BotClientRetryableError("HTTP 500")

    max_backoff = 0.08
    resilience = ResilienceConfig(
        retry=RetryConfig(
            max_attempts=4,
            backoff_seconds=0.05,
            backoff_strategy="exponential",
            backoff_multiplier=10.0,
            max_backoff_seconds=max_backoff,
        ),
    )
    sender = BotHttpSender.__new__(BotHttpSender)
    sender._retry = resilience.retry
    from aiobreaker import CircuitBreaker

    sender._cb = CircuitBreaker(fail_max=10, timeout_duration=timedelta(seconds=60))
    sender._client = MagicMock()
    sender._client.send_update = fake_send

    await sender.send_update(UPDATE)

    for i in range(1, len(timestamps) - 1):
        gap = timestamps[i + 1] - timestamps[i]
        assert gap <= max_backoff * 2.0
