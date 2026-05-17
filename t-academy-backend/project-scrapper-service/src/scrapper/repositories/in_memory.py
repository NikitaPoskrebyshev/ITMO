from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..models.models import TrackedLink
from .repository import (
    ChatAlreadyExistsError,
    ChatNotFoundError,
    LinkAlreadyExistsError,
    LinkNotFoundError,
    ScrapperRepository,
)


@dataclass(slots=True)
class InMemoryRepository(ScrapperRepository):
    _chats: set[int] = field(default_factory=set)
    _links: dict[str, TrackedLink] = field(default_factory=dict)
    _chat_links: dict[int, set[str]] = field(default_factory=dict)

    async def register_chat(self, chat_id: int) -> None:
        if chat_id in self._chats:
            raise ChatAlreadyExistsError(f"Chat {chat_id} already exists")
        self._chats.add(chat_id)
        self._chat_links[chat_id] = set()

    async def delete_chat(self, chat_id: int) -> None:
        if chat_id not in self._chats:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        self._chats.remove(chat_id)
        for url in list(self._chat_links.get(chat_id, set())):
            if url in self._links:
                self._links[url].chat_ids.discard(chat_id)
                if not self._links[url].chat_ids:
                    del self._links[url]
        self._chat_links.pop(chat_id, None)

    async def get_links_for_chat(self, chat_id: int) -> list[TrackedLink]:
        if chat_id not in self._chats:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        return [
            self._links[url]
            for url in self._chat_links.get(chat_id, set())
            if url in self._links
        ]

    async def add_link(
        self,
        chat_id: int,
        url: str,
        link_type: str,
        tags: list[str],
        filters: list[str] | None = None,
    ) -> TrackedLink:
        if chat_id not in self._chats:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        if url in self._chat_links.get(chat_id, set()):
            raise LinkAlreadyExistsError(
                f"Link {url} is already tracked for chat {chat_id}"
            )
        if url not in self._links:
            self._links[url] = TrackedLink(
                url=url,
                link_type=link_type,
                tags=list(tags),
                filters=list(filters or []),
            )
        self._links[url].chat_ids.add(chat_id)
        self._chat_links[chat_id].add(url)
        return self._links[url]

    async def remove_link(self, chat_id: int, url: str) -> TrackedLink:
        if chat_id not in self._chats:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        if url not in self._chat_links.get(chat_id, set()):
            raise LinkNotFoundError(f"Link {url} not found for chat {chat_id}")
        self._chat_links[chat_id].discard(url)
        stored = self._links[url]
        stored.chat_ids.discard(chat_id)
        if not stored.chat_ids:
            del self._links[url]
        return stored

    async def get_all_links(
        self, limit: int = 100, offset: int = 0
    ) -> list[TrackedLink]:
        all_links = list(self._links.values())
        return all_links[offset : offset + limit]

    async def update_link_state(self, url: str, last_known_update: str) -> None:
        if url in self._links:
            self._links[url].last_known_update = last_known_update
            self._links[url].last_checked_at = datetime.now()
