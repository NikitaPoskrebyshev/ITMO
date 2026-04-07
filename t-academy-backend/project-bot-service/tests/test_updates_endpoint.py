from __future__ import annotations

import json

import pytest

from bot.web_server import UpdatesServer


class FakeBot:
    def __init__(self) -> None:
        self.sent_messages: list[dict] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent_messages.append({"chat_id": chat_id, "text": text})


def make_server(bot=None) -> UpdatesServer:
    if bot is None:
        bot = FakeBot()
    return UpdatesServer(host="127.0.0.1", port=0, bot=bot)


async def _call_handle_updates(server: UpdatesServer, body: bytes) -> tuple[int, bytes]:
    return await server._handle_updates(body)


@pytest.mark.asyncio
async def test_valid_update_returns_200_and_notifies_chats() -> None:
    bot = FakeBot()
    server = make_server(bot)
    payload = json.dumps(
        {
            "id": 1,
            "url": "https://github.com/owner/repo",
            "description": "New commit pushed",
            "tg_chat_ids": [100, 200],
        }
    ).encode()

    status, _ = await _call_handle_updates(server, payload)

    assert status == 200
    assert len(bot.sent_messages) == 2
    chat_ids = {m["chat_id"] for m in bot.sent_messages}
    assert chat_ids == {100, 200}
    for msg in bot.sent_messages:
        assert "https://github.com/owner/repo" in msg["text"]
        assert "New commit pushed" in msg["text"]


@pytest.mark.asyncio
async def test_invalid_json_returns_400() -> None:
    server = make_server()
    status, body = await _call_handle_updates(server, b"not valid json{")

    assert status == 400


@pytest.mark.asyncio
async def test_missing_fields_returns_400() -> None:
    server = make_server()
    payload = json.dumps({"id": 1, "url": "https://github.com/a/b"}).encode()

    status, body = await _call_handle_updates(server, payload)

    assert status == 400


@pytest.mark.asyncio
async def test_invalid_tg_chat_ids_type_returns_400() -> None:
    server = make_server()
    payload = json.dumps(
        {
            "id": 1,
            "url": "https://github.com/a/b",
            "description": "update",
            "tg_chat_ids": "not-a-list",
        }
    ).encode()

    status, _ = await _call_handle_updates(server, payload)

    assert status == 400


@pytest.mark.asyncio
async def test_notification_failure_does_not_crash_server() -> None:
    bot = FakeBot()

    async def failing_send(chat_id: int, text: str) -> None:
        raise RuntimeError("Telegram API down")

    bot.send_message = failing_send  # type: ignore[method-assign]

    server = make_server(bot)
    payload = json.dumps(
        {
            "id": 1,
            "url": "https://github.com/a/b",
            "description": "update",
            "tg_chat_ids": [42],
        }
    ).encode()

    status, _ = await _call_handle_updates(server, payload)

    assert status == 200
