from __future__ import annotations

import logging

from ..models.models import AddLinkRequest, RemoveLinkRequest, TrackedLink
from ..repositories.repository import InMemoryRepository
from .link_parser import GitHubLink, parse_link

logger = logging.getLogger(__name__)


class LinkService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self._repository = repository

    def add_link(self, chat_id: int, request: AddLinkRequest) -> TrackedLink:
        parsed = parse_link(request.link)  # raises InvalidLinkError if unsupported
        link_type = "github" if isinstance(parsed, GitHubLink) else "stackoverflow"
        link = self._repository.add_link(chat_id, request.link, link_type, list(request.tags))
        logger.info("link_added", extra={"chat_id": chat_id, "url": request.link})
        return link

    def remove_link(self, chat_id: int, request: RemoveLinkRequest) -> TrackedLink:
        link = self._repository.remove_link(chat_id, request.link)
        logger.info("link_removed", extra={"chat_id": chat_id, "url": request.link})
        return link

    def get_links(self, chat_id: int) -> list[TrackedLink]:
        return self._repository.get_links_for_chat(chat_id)
