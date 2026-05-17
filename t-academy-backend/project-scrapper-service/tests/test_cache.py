from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from scrapper.app import create_app
from scrapper.cache.cache import LinkCache
from scrapper.config.config import AppConfig, ValkeyConfig


def _make_producer_mock() -> AsyncMock:
    producer = AsyncMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    producer.send_and_wait = AsyncMock()
    return producer


async def test_cache_miss_returns_none(redis_url: str) -> None:
    cache = LinkCache(url=redis_url, ttl_seconds=60)
    await cache.start()
    result = await cache.get(chat_id=9999)
    await cache.stop()
    assert result is None


async def test_cache_set_and_get(redis_url: str) -> None:
    cache = LinkCache(url=redis_url, ttl_seconds=60)
    await cache.start()
    await cache.set(
        chat_id=1,
        value='[{"url": "https://github.com/x/y", "link_type": "github", "tags": [], "filters": []}]',
    )
    result = await cache.get(chat_id=1)
    await cache.stop()
    assert result is not None
    assert "github.com/x/y" in result


async def test_cache_invalidate(redis_url: str) -> None:
    cache = LinkCache(url=redis_url, ttl_seconds=60)
    await cache.start()
    await cache.set(chat_id=2, value="[]")
    await cache.invalidate(chat_id=2)
    result = await cache.get(chat_id=2)
    await cache.stop()
    assert result is None


async def test_cache_different_chat_ids_are_independent(redis_url: str) -> None:
    cache = LinkCache(url=redis_url, ttl_seconds=60)
    await cache.start()
    await cache.set(chat_id=10, value="[1]")
    await cache.set(chat_id=11, value="[2]")
    await cache.invalidate(chat_id=10)
    assert await cache.get(chat_id=10) is None
    assert await cache.get(chat_id=11) is not None
    await cache.stop()


GITHUB_URL = "https://github.com/octocat/Hello-World"
CHAT_ID = 555


@pytest.fixture
def cached_app(redis_url: str, mocker):  # type: ignore[no-untyped-def]
    mocker.patch("scrapper.scheduler.scheduler.Scheduler.start")
    mocker.patch("scrapper.scheduler.scheduler.Scheduler.stop")
    mocker.patch(
        "scrapper.clients.kafka_sender.AIOKafkaProducer",
        return_value=_make_producer_mock(),
    )
    config = AppConfig(valkey=ValkeyConfig(url=redis_url, ttl_seconds=30))
    return create_app(config)


@pytest_asyncio.fixture
async def cached_client(cached_app) -> AsyncClient:  # type: ignore[misc]
    async with cached_app.router.lifespan_context(cached_app):
        async with AsyncClient(
            transport=ASGITransport(app=cached_app), base_url="http://test"
        ) as c:
            yield c


async def test_get_links_result_is_cached(
    cached_client: AsyncClient, redis_url: str
) -> None:
    await cached_client.post(f"/tg-chat/{CHAT_ID}")
    await cached_client.post(
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": str(CHAT_ID)},
    )

    response = await cached_client.get("/links", headers={"Tg-Chat-Id": str(CHAT_ID)})
    assert response.status_code == 200
    assert response.json()["size"] == 1

    cache = LinkCache(url=redis_url, ttl_seconds=30)
    await cache.start()
    cached = await cache.get(CHAT_ID)
    await cache.stop()

    assert cached is not None
    assert GITHUB_URL in cached


async def test_cache_invalidated_on_add_link(
    cached_client: AsyncClient, redis_url: str
) -> None:
    chat_id = 556
    await cached_client.post(f"/tg-chat/{chat_id}")

    await cached_client.get("/links", headers={"Tg-Chat-Id": str(chat_id)})

    cache = LinkCache(url=redis_url, ttl_seconds=30)
    await cache.start()

    await cached_client.post(
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": str(chat_id)},
    )
    after = await cache.get(chat_id)
    await cache.stop()

    assert after is None


async def test_cache_invalidated_on_remove_link(
    cached_client: AsyncClient, redis_url: str
) -> None:
    chat_id = 557
    await cached_client.post(f"/tg-chat/{chat_id}")
    await cached_client.post(
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": str(chat_id)},
    )

    await cached_client.get("/links", headers={"Tg-Chat-Id": str(chat_id)})

    await cached_client.request(
        "DELETE",
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": str(chat_id)},
    )

    cache = LinkCache(url=redis_url, ttl_seconds=30)
    await cache.start()
    result = await cache.get(chat_id)
    await cache.stop()

    assert result is None
