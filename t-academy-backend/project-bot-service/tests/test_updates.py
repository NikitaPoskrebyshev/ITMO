from __future__ import annotations

import pytest

from bot.http_server import handle_updates_request
from bot.models import LinkUpdate


@pytest.mark.asyncio
async def test_valid_update_returns_200() -> None:
    received: list[LinkUpdate] = []

    async def on_update(update: LinkUpdate) -> None:
        received.append(update)

    body = b'{"id": 1, "url": "https://github.com/u/r", "description": "updated", "tgChatIds": [42, 99]}'
    status = await handle_updates_request(body, on_update)

    assert status == 200
    assert len(received) == 1
    assert received[0].id == 1
    assert received[0].url == "https://github.com/u/r"
    assert received[0].tg_chat_ids == [42, 99]


@pytest.mark.asyncio
async def test_invalid_json_returns_400() -> None:
    async def on_update(update: LinkUpdate) -> None:
        pass

    status = await handle_updates_request(b"not json at all", on_update)
    assert status == 400


@pytest.mark.asyncio
async def test_missing_field_returns_400() -> None:
    async def on_update(update: LinkUpdate) -> None:
        pass

    body = (
        b'{"id": 1, "url": "https://github.com/u/r"}'  # missing description + tgChatIds
    )
    status = await handle_updates_request(body, on_update)
    assert status == 400


@pytest.mark.asyncio
async def test_empty_body_returns_400() -> None:
    async def on_update(update: LinkUpdate) -> None:
        pass

    status = await handle_updates_request(b"", on_update)
    assert status == 400


@pytest.mark.asyncio
async def test_non_object_json_returns_400() -> None:
    async def on_update(update: LinkUpdate) -> None:
        pass

    status = await handle_updates_request(b"[1, 2, 3]", on_update)
    assert status == 400


@pytest.mark.asyncio
async def test_handler_exception_returns_400() -> None:
    async def on_update(update: LinkUpdate) -> None:
        raise RuntimeError("unexpected error")

    body = b'{"id": 1, "url": "https://github.com/u/r", "description": "d", "tgChatIds": [1]}'
    status = await handle_updates_request(body, on_update)
    assert status == 400


def test_link_update_from_dict_valid() -> None:
    data = {"id": 5, "url": "https://x.com", "description": "desc", "tgChatIds": [1, 2]}
    update = LinkUpdate.from_dict(data)
    assert update.id == 5
    assert update.tg_chat_ids == [1, 2]


def test_link_update_from_dict_missing_field_raises() -> None:
    data = {"id": 5, "url": "https://x.com"}
    with pytest.raises(ValueError):
        LinkUpdate.from_dict(data)
