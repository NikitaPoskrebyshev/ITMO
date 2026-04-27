from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models.models import LinkUpdate
from .bot_client import BotClient


@runtime_checkable
class MessageSender(Protocol):
    async def send_update(self, update: LinkUpdate) -> None: ...


class BotHttpSender(MessageSender):
    def __init__(self, bot_client: BotClient) -> None:
        self._client = bot_client

    async def send_update(self, update: LinkUpdate) -> None:
        await self._client.send_update(update)
