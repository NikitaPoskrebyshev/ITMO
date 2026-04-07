from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from scrapper.clients.bot_client import BotClient
from scrapper.clients.github_client import GitHubClient
from scrapper.clients.stackoverflow_client import StackOverflowClient
from scrapper.models.models import LinkUpdate


def _mock_http_client(response: MagicMock) -> AsyncMock:
    """Return an AsyncMock that behaves like httpx.AsyncClient context manager."""
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.get.return_value = response
    mock.post.return_value = response
    return mock


# --- GitHubClient ---

async def test_github_client_returns_updated_at(mocker) -> None:  # type: ignore[no-untyped-def]
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"updated_at": "2024-01-01T00:00:00Z"}

    mocker.patch("scrapper.clients.github_client.httpx.AsyncClient", return_value=_mock_http_client(response))

    result = await GitHubClient().get_last_update("octocat", "Hello-World")
    assert result == "2024-01-01T00:00:00Z"


async def test_github_client_non_2xx_returns_none(mocker) -> None:  # type: ignore[no-untyped-def]
    response = MagicMock()
    response.status_code = 404

    mocker.patch("scrapper.clients.github_client.httpx.AsyncClient", return_value=_mock_http_client(response))

    result = await GitHubClient().get_last_update("octocat", "nonexistent")
    assert result is None


async def test_github_client_http_error_returns_none(mocker) -> None:  # type: ignore[no-untyped-def]
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.get.side_effect = httpx.HTTPError("timeout")

    mocker.patch("scrapper.clients.github_client.httpx.AsyncClient", return_value=mock)

    result = await GitHubClient().get_last_update("octocat", "Hello-World")
    assert result is None


async def test_github_client_invalid_json_returns_none(mocker) -> None:  # type: ignore[no-untyped-def]
    response = MagicMock()
    response.status_code = 200
    response.json.side_effect = ValueError("invalid json")

    mocker.patch("scrapper.clients.github_client.httpx.AsyncClient", return_value=_mock_http_client(response))

    result = await GitHubClient().get_last_update("octocat", "Hello-World")
    assert result is None


# --- StackOverflowClient ---

async def test_stackoverflow_client_returns_last_activity(mocker) -> None:  # type: ignore[no-untyped-def]
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"items": [{"last_activity_date": 1704067200}]}

    mocker.patch("scrapper.clients.stackoverflow_client.httpx.AsyncClient", return_value=_mock_http_client(response))

    result = await StackOverflowClient().get_last_update(11227809)
    assert result == "1704067200"


async def test_stackoverflow_client_non_2xx_returns_none(mocker) -> None:  # type: ignore[no-untyped-def]
    response = MagicMock()
    response.status_code = 400

    mocker.patch("scrapper.clients.stackoverflow_client.httpx.AsyncClient", return_value=_mock_http_client(response))

    result = await StackOverflowClient().get_last_update(11227809)
    assert result is None


async def test_stackoverflow_client_empty_items_returns_none(mocker) -> None:  # type: ignore[no-untyped-def]
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"items": []}

    mocker.patch("scrapper.clients.stackoverflow_client.httpx.AsyncClient", return_value=_mock_http_client(response))

    result = await StackOverflowClient().get_last_update(11227809)
    assert result is None


async def test_stackoverflow_client_http_error_returns_none(mocker) -> None:  # type: ignore[no-untyped-def]
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.get.side_effect = httpx.HTTPError("timeout")

    mocker.patch("scrapper.clients.stackoverflow_client.httpx.AsyncClient", return_value=mock)

    result = await StackOverflowClient().get_last_update(11227809)
    assert result is None


# --- BotClient ---

async def test_bot_client_sends_update(mocker) -> None:  # type: ignore[no-untyped-def]
    response = MagicMock()
    response.status_code = 200

    mocker.patch("scrapper.clients.bot_client.httpx.AsyncClient", return_value=_mock_http_client(response))

    update = LinkUpdate(id=1, url="https://github.com/x/y", description="update", tg_chat_ids=[42])
    await BotClient(base_url="http://bot:8081").send_update(update)  # should not raise


async def test_bot_client_non_2xx_does_not_raise(mocker) -> None:  # type: ignore[no-untyped-def]
    response = MagicMock()
    response.status_code = 500

    mocker.patch("scrapper.clients.bot_client.httpx.AsyncClient", return_value=_mock_http_client(response))

    update = LinkUpdate(id=1, url="https://github.com/x/y", description="update", tg_chat_ids=[42])
    await BotClient(base_url="http://bot:8081").send_update(update)  # should not raise


async def test_bot_client_http_error_does_not_raise(mocker) -> None:  # type: ignore[no-untyped-def]
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.post.side_effect = httpx.HTTPError("connection refused")

    mocker.patch("scrapper.clients.bot_client.httpx.AsyncClient", return_value=mock)

    update = LinkUpdate(id=1, url="https://github.com/x/y", description="update", tg_chat_ids=[42])
    await BotClient(base_url="http://bot:8081").send_update(update)  # should not raise
