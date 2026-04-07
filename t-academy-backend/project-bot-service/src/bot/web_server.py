from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from bot.models import LinkUpdate

if TYPE_CHECKING:
    from telegram import Bot

logger = logging.getLogger(__name__)


class UpdatesServer:
    def __init__(self, host: str, port: int, bot: Bot) -> None:
        self._host = host
        self._port = port
        self._bot = bot

    async def serve(self) -> None:
        server = await asyncio.start_server(
            self._handle_client, self._host, self._port
        )
        logger.info(
            "Updates server started",
            extra={"event": "updates_server_started", "host": self._host, "port": self._port},
        )
        async with server:
            await server.serve_forever()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            request_line = (await reader.readline()).decode("utf-8", errors="replace")
            if not request_line.strip():
                return

            parts = request_line.strip().split(" ")
            if len(parts) < 2:
                return
            method, path = parts[0], parts[1]

            headers: dict[str, str] = {}
            while True:
                line = (await reader.readline()).decode("utf-8", errors="replace")
                if line in ("\r\n", "\n", ""):
                    break
                if ":" in line:
                    key, val = line.split(":", 1)
                    headers[key.strip().lower()] = val.strip()

            content_length = int(headers.get("content-length", 0))
            body = b""
            if content_length > 0:
                body = await reader.readexactly(content_length)

            if method == "POST" and path == "/updates":
                status, response_body = await self._handle_updates(body)
            else:
                status, response_body = 404, b'{"description": "Not found"}'

            response = (
                f"HTTP/1.1 {status}\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Content-Type: application/json\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode() + response_body
            writer.write(response)
            await writer.drain()
        except Exception:
            logger.exception(
                "Error handling HTTP request",
                extra={"event": "updates_handler_error"},
            )
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_updates(self, body: bytes) -> tuple[int, bytes]:
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.info(
                "Invalid JSON in /updates request",
                extra={"event": "updates_validation_failed", "reason": "invalid_json"},
            )
            return 400, b'{"description": "Invalid JSON"}'

        required_fields = ("id", "url", "description", "tg_chat_ids")
        if not all(k in data for k in required_fields):
            missing = [k for k in required_fields if k not in data]
            logger.info(
                "Missing fields in /updates request",
                extra={"event": "updates_validation_failed", "missing": str(missing)},
            )
            return 400, b'{"description": "Missing required fields"}'

        if not isinstance(data["tg_chat_ids"], list):
            logger.info(
                "Invalid tg_chat_ids in /updates request",
                extra={"event": "updates_validation_failed", "reason": "tg_chat_ids_not_list"},
            )
            return 400, b'{"description": "tg_chat_ids must be a list"}'

        update = LinkUpdate(
            id=data["id"],
            url=data["url"],
            description=data["description"],
            tg_chat_ids=data["tg_chat_ids"],
        )

        logger.info(
            "Update notification received",
            extra={
                "event": "updates_received",
                "url": update.url,
                "chat_count": len(update.tg_chat_ids),
            },
        )

        for chat_id in update.tg_chat_ids:
            try:
                text = f"Обновление по ссылке {update.url}:\n{update.description}"
                await self._bot.send_message(chat_id=chat_id, text=text)
            except Exception:
                logger.exception(
                    "Failed to send update notification",
                    extra={"event": "notification_failed", "chat_id": chat_id},
                )

        return 200, b"{}"
