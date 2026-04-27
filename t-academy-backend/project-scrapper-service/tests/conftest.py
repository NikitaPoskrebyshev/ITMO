import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from scrapper.app import create_app
from scrapper.config.config import AppConfig


@pytest.fixture
def config() -> AppConfig:
    return AppConfig()


@pytest.fixture
def app(config: AppConfig, mocker):  # type: ignore[no-untyped-def]
    mocker.patch("scrapper.scheduler.scheduler.Scheduler.start")
    mocker.patch("scrapper.scheduler.scheduler.Scheduler.stop")
    return create_app(config)


@pytest_asyncio.fixture
async def client(app) -> AsyncClient:  # type: ignore[misc]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
