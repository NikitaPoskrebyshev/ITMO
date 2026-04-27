from __future__ import annotations

import logging

from ..repositories.repository import ScrapperRepository

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, repository: ScrapperRepository) -> None:
        self._repository = repository

    async def register_chat(self, chat_id: int) -> None:
        await self._repository.register_chat(chat_id)
        logger.info("chat_registered", extra={"chat_id": chat_id})

    async def delete_chat(self, chat_id: int) -> None:
        await self._repository.delete_chat(chat_id)
        logger.info("chat_deleted", extra={"chat_id": chat_id})
