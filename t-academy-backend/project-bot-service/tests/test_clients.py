from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.clients import (
    ChatNotFoundError,
    LinkAlreadyTrackedError,
    LinkNotFoundError,
    ScrapperClientError,
    ScrapperHttpClient,
)
from bot.models import LinkResponse


def make_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    if json_data is not None:
        resp.json.return_value = json_data
    return resp


@pytest.fixture
def client() -> ScrapperHttpClient:
    return ScrapperHttpClient(base_url="http://scrapper:8080", timeout_seconds=5)


@pytest.mark.asyncio
async def test_register_chat_success(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=make_response(200))
        mock_cls.return_value = mock_http

        await client.register_chat(42)

        mock_http.post.assert_called_once_with("http://scrapper:8080/tg-chat/42")


@pytest.mark.asyncio
async def test_register_chat_error_raises(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=make_response(500))
        mock_cls.return_value = mock_http

        with pytest.raises(ScrapperClientError):
            await client.register_chat(42)


@pytest.mark.asyncio
async def test_add_link_success(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(
            return_value=make_response(
                200, {"id": 1, "url": "https://github.com/u/r", "tags": ["t"]}
            )
        )
        mock_cls.return_value = mock_http

        result = await client.add_link(100, "https://github.com/u/r", ["t"], [])

        assert isinstance(result, LinkResponse)
        assert result.url == "https://github.com/u/r"
        assert result.tags == ["t"]


@pytest.mark.asyncio
async def test_add_link_duplicate_raises(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=make_response(409))
        mock_cls.return_value = mock_http

        with pytest.raises(LinkAlreadyTrackedError):
            await client.add_link(100, "https://github.com/u/r", [], [])


@pytest.mark.asyncio
async def test_add_link_chat_not_found_raises(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=make_response(404))
        mock_cls.return_value = mock_http

        with pytest.raises(ChatNotFoundError):
            await client.add_link(100, "https://github.com/u/r", [], [])


@pytest.mark.asyncio
async def test_remove_link_success(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.request = AsyncMock(
            return_value=make_response(
                200, {"id": 1, "url": "https://github.com/u/r", "tags": []}
            )
        )
        mock_cls.return_value = mock_http

        result = await client.remove_link(100, "https://github.com/u/r")

        assert result.url == "https://github.com/u/r"


@pytest.mark.asyncio
async def test_remove_link_not_found_raises(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.request = AsyncMock(return_value=make_response(404))
        mock_cls.return_value = mock_http

        with pytest.raises(LinkNotFoundError):
            await client.remove_link(100, "https://github.com/u/r")


@pytest.mark.asyncio
async def test_list_links_success(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(
            return_value=make_response(
                200,
                {
                    "links": [{"id": 1, "url": "https://github.com/u/r", "tags": []}],
                    "size": 1,
                },
            )
        )
        mock_cls.return_value = mock_http

        results = await client.list_links(100)

        assert len(results) == 1
        assert results[0].url == "https://github.com/u/r"


@pytest.mark.asyncio
async def test_list_links_server_error_raises(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=make_response(503))
        mock_cls.return_value = mock_http

        with pytest.raises(ScrapperClientError):
            await client.list_links(100)


@pytest.mark.asyncio
async def test_list_links_network_failure_raises(client: ScrapperHttpClient) -> None:
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_cls.return_value = mock_http

        with pytest.raises(httpx.ConnectError):
            await client.list_links(100)
