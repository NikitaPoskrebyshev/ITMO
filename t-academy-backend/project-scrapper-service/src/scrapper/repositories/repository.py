from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..models.models import TrackedLink


class ChatNotFoundError(Exception):
    pass


class LinkNotFoundError(Exception):
    pass


class LinkAlreadyExistsError(Exception):
    pass


@dataclass(slots=True)
class InMemoryRepository:
    _chats: set[int] = field(default_factory=set)
    _links: dict[str, TrackedLink] = field(default_factory=dict)
    _chat_links: dict[int, set[str]] = field(default_factory=dict)

    def register_chat(self, chat_id: int) -> None:
        self._chats.add(chat_id)
        if chat_id not in self._chat_links:
            self._chat_links[chat_id] = set()

    def delete_chat(self, chat_id: int) -> None:
        if chat_id not in self._chats:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        self._chats.remove(chat_id)
        for url in list(self._chat_links.get(chat_id, set())):
            if url in self._links:
                self._links[url].chat_ids.discard(chat_id)
                if not self._links[url].chat_ids:
                    del self._links[url]
        self._chat_links.pop(chat_id, None)

    def chat_exists(self, chat_id: int) -> bool:
        return chat_id in self._chats

    def get_links_for_chat(self, chat_id: int) -> list[TrackedLink]:
        if chat_id not in self._chats:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        return [
            self._links[url]
            for url in self._chat_links.get(chat_id, set())
            if url in self._links
        ]

    def add_link(self, chat_id: int, url: str, link_type: str, tags: list[str]) -> TrackedLink:
        if chat_id not in self._chats:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        if url in self._chat_links.get(chat_id, set()):
            raise LinkAlreadyExistsError(f"Link {url} is already tracked for chat {chat_id}")
        if url not in self._links:
            self._links[url] = TrackedLink(url=url, link_type=link_type, tags=list(tags))
        self._links[url].chat_ids.add(chat_id)
        if chat_id not in self._chat_links:
            self._chat_links[chat_id] = set()
        self._chat_links[chat_id].add(url)
        return self._links[url]

    def remove_link(self, chat_id: int, url: str) -> TrackedLink:
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

    def get_all_links(self) -> list[TrackedLink]:
        return list(self._links.values())

    def update_link_state(self, url: str, last_known_update: str) -> None:
        if url in self._links:
            self._links[url].last_known_update = last_known_update
            self._links[url].last_checked_at = datetime.now()
