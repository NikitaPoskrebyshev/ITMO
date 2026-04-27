from __future__ import annotations

import logging

from ..models.models import AddLinkRequest, RemoveLinkRequest, TrackedLink
from ..repositories.repository import ScrapperRepository
from .link_parser import GitHubLink, parse_link

logger = logging.getLogger(__name__)


class LinkService:
    def __init__(self, repository: ScrapperRepository) -> None:
        self._repository = repository

    async def add_link(self, chat_id: int, request: AddLinkRequest) -> TrackedLink:
        parsed = parse_link(request.link)
        link_type = "github" if isinstance(parsed, GitHubLink) else "stackoverflow"
        link = await self._repository.add_link(
            chat_id, request.link, link_type, list(request.tags), list(request.filters)
        )
        logger.info("link_added", extra={"chat_id": chat_id, "url": request.link})
        return link

    async def remove_link(
        self, chat_id: int, request: RemoveLinkRequest
    ) -> TrackedLink:
        link = await self._repository.remove_link(chat_id, request.link)
        logger.info("link_removed", extra={"chat_id": chat_id, "url": request.link})
        return link

    async def get_links(self, chat_id: int) -> list[TrackedLink]:
        return await self._repository.get_links_for_chat(chat_id)
