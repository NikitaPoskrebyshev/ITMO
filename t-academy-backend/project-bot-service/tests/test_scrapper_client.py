from __future__ import annotations

import json
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from bot.models import AddLinkRequest, RemoveLinkRequest
from bot.scrapper_client import (
    ChatNotFoundError,
    DuplicateLinkError,
    InvalidLinkError,
    LinkNotFoundError,
    ScrapperHttpClient,
)


def make_client() -> ScrapperHttpClient:
    return ScrapperHttpClient(base_url="http://localhost:8080", timeout_seconds=5)


def fake_urlopen_response(data: dict):
    content = json.dumps(data).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = content
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def fake_http_error(status: int, body: dict) -> urllib.error.HTTPError:
    content = json.dumps(body).encode()
    err = urllib.error.HTTPError(
        url="http://example.com",
        code=status,
        msg="error",
        hdrs=MagicMock(),  # type: ignore[arg-type]
        fp=BytesIO(content),
    )
    return err


# ---- register_chat ----


@pytest.mark.asyncio
async def test_register_chat_success() -> None:
    client = make_client()
    with patch("urllib.request.urlopen", return_value=fake_urlopen_response({})):
        await client.register_chat(chat_id=100)


# ---- add_link ----


@pytest.mark.asyncio
async def test_add_link_success() -> None:
    client = make_client()
    response_data = {"id": 1, "url": "https://github.com/a/b", "tags": ["python"]}
    with patch("urllib.request.urlopen", return_value=fake_urlopen_response(response_data)):
        result = await client.add_link(100, AddLinkRequest(link="https://github.com/a/b", tags=["python"]))

    assert result.url == "https://github.com/a/b"
    assert result.tags == ["python"]
    assert result.id == 1


@pytest.mark.asyncio
async def test_add_link_raises_duplicate_error() -> None:
    client = make_client()
    with patch(
        "urllib.request.urlopen",
        side_effect=fake_http_error(400, {"detail": "Link is already tracked for this chat"}),
    ):
        with pytest.raises(DuplicateLinkError):
            await client.add_link(100, AddLinkRequest(link="https://github.com/a/b"))


@pytest.mark.asyncio
async def test_add_link_raises_invalid_link_error() -> None:
    client = make_client()
    with patch(
        "urllib.request.urlopen",
        side_effect=fake_http_error(400, {"detail": "Unsupported link type"}),
    ):
        with pytest.raises(InvalidLinkError):
            await client.add_link(100, AddLinkRequest(link="https://example.com"))


@pytest.mark.asyncio
async def test_add_link_raises_chat_not_found() -> None:
    client = make_client()
    with patch(
        "urllib.request.urlopen",
        side_effect=fake_http_error(404, {"detail": "Chat not found"}),
    ):
        with pytest.raises(ChatNotFoundError):
            await client.add_link(100, AddLinkRequest(link="https://github.com/a/b"))


# ---- remove_link ----


@pytest.mark.asyncio
async def test_remove_link_success() -> None:
    client = make_client()
    response_data = {"id": 1, "url": "https://github.com/a/b", "tags": []}
    with patch("urllib.request.urlopen", return_value=fake_urlopen_response(response_data)):
        result = await client.remove_link(100, RemoveLinkRequest(link="https://github.com/a/b"))

    assert result.url == "https://github.com/a/b"


@pytest.mark.asyncio
async def test_remove_link_not_found() -> None:
    client = make_client()
    with patch(
        "urllib.request.urlopen",
        side_effect=fake_http_error(404, {"detail": "Link not found"}),
    ):
        with pytest.raises(LinkNotFoundError):
            await client.remove_link(100, RemoveLinkRequest(link="https://github.com/a/b"))


# ---- list_links ----


@pytest.mark.asyncio
async def test_list_links_success() -> None:
    client = make_client()
    response_data = {
        "links": [
            {"id": 1, "url": "https://github.com/a/b", "tags": ["tag1"]},
            {"id": 2, "url": "https://stackoverflow.com/questions/1", "tags": []},
        ],
        "size": 2,
    }
    with patch("urllib.request.urlopen", return_value=fake_urlopen_response(response_data)):
        result = await client.list_links(100)

    assert result.size == 2
    assert len(result.links) == 2
    assert result.links[0].url == "https://github.com/a/b"
    assert result.links[0].tags == ["tag1"]


@pytest.mark.asyncio
async def test_list_links_chat_not_found() -> None:
    client = make_client()
    with patch(
        "urllib.request.urlopen",
        side_effect=fake_http_error(404, {"detail": "Chat not found"}),
    ):
        with pytest.raises(ChatNotFoundError):
            await client.list_links(999)


# ---- network failure ----


@pytest.mark.asyncio
async def test_network_failure_raises_scrapper_error() -> None:
    client = make_client()
    import urllib.error

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Connection refused"),
    ):
        with pytest.raises(Exception):
            await client.register_chat(100)
