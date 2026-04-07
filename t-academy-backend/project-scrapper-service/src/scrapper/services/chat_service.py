from __future__ import annotations

import logging

from ..repositories.repository import InMemoryRepository

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self._repository = repository

    def register_chat(self, chat_id: int) -> None:
        self._repository.register_chat(chat_id)
        logger.info("chat_registered", extra={"chat_id": chat_id})

    def delete_chat(self, chat_id: int) -> None:
        self._repository.delete_chat(chat_id)
        logger.info("chat_deleted", extra={"chat_id": chat_id})
