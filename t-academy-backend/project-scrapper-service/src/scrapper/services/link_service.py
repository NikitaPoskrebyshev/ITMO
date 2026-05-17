from __future__ import annotations

import json
import logging

from ..cache.cache import LinkCache
from ..models.models import AddLinkRequest, RemoveLinkRequest, TrackedLink
from ..repositories.repository import ScrapperRepository
from .link_parser import GitHubLink, parse_link

logger = logging.getLogger(__name__)


class LinkService:
    def __init__(
        self, repository: ScrapperRepository, cache: LinkCache | None = None
    ) -> None:
        self._repository = repository
        self._cache = cache

    async def add_link(self, chat_id: int, request: AddLinkRequest) -> TrackedLink:
        parsed = parse_link(request.link)
        link_type = "github" if isinstance(parsed, GitHubLink) else "stackoverflow"
        link = await self._repository.add_link(
            chat_id, request.link, link_type, list(request.tags), list(request.filters)
        )
        if self._cache is not None:
            await self._cache.invalidate(chat_id)
        logger.info("link_added", extra={"chat_id": chat_id, "url": request.link})
        return link

    async def remove_link(
        self, chat_id: int, request: RemoveLinkRequest
    ) -> TrackedLink:
        link = await self._repository.remove_link(chat_id, request.link)
        if self._cache is not None:
            await self._cache.invalidate(chat_id)
        logger.info("link_removed", extra={"chat_id": chat_id, "url": request.link})
        return link

    async def get_links(self, chat_id: int) -> list[TrackedLink]:
        if self._cache is not None:
            cached = await self._cache.get(chat_id)
            if cached is not None:
                raw = json.loads(cached)
                return [
                    TrackedLink(
                        url=item["url"],
                        link_type=item["link_type"],
                        tags=item.get("tags", []),
                        filters=item.get("filters", []),
                    )
                    for item in raw
                ]

        links = await self._repository.get_links_for_chat(chat_id)

        if self._cache is not None:
            payload = json.dumps(
                [
                    {
                        "url": lnk.url,
                        "link_type": lnk.link_type,
                        "tags": lnk.tags,
                        "filters": lnk.filters,
                    }
                    for lnk in links
                ]
            )
            await self._cache.set(chat_id, payload)

        return links
