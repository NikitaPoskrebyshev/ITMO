from __future__ import annotations

import asyncio
import logging

from ..clients.bot_client import BotClient
from ..clients.github_client import GitHubClient
from ..clients.stackoverflow_client import StackOverflowClient
from ..models.models import LinkUpdate, TrackedLink
from ..repositories.repository import InMemoryRepository
from ..services.link_parser import GitHubLink, InvalidLinkError, StackOverflowLink, parse_link

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(
        self,
        repository: InMemoryRepository,
        github_client: GitHubClient,
        stackoverflow_client: StackOverflowClient,
        bot_client: BotClient,
        interval_seconds: int = 60,
    ) -> None:
        self._repository = repository
        self._github_client = github_client
        self._stackoverflow_client = stackoverflow_client
        self._bot_client = bot_client
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None

    async def _fetch_update(self, link: TrackedLink) -> str | None:
        try:
            parsed = parse_link(link.url)
        except InvalidLinkError:
            return None
        if isinstance(parsed, GitHubLink):
            return await self._github_client.get_last_update(parsed.owner, parsed.repo)
        if isinstance(parsed, StackOverflowLink):
            return await self._stackoverflow_client.get_last_update(parsed.question_id)
        return None

    async def _check_link(self, link: TrackedLink) -> None:
        try:
            current = await self._fetch_update(link)
        except Exception as exc:
            logger.error("external_api_failed", extra={"url": link.url, "error": str(exc)})
            return
        if current is None:
            return
        if link.last_known_update != current:
            logger.info("update_detected", extra={"url": link.url})
            update = LinkUpdate(
                id=abs(hash(link.url)),
                url=link.url,
                description=f"Update detected for {link.url}",
                tg_chat_ids=list(link.chat_ids),
            )
            await self._bot_client.send_update(update)
            self._repository.update_link_state(link.url, current)

    async def _run(self) -> None:
        while True:
            try:
                for link in self._repository.get_all_links():
                    await self._check_link(link)
            except Exception as exc:
                logger.error("scheduler_error", extra={"error": str(exc)})
            await asyncio.sleep(self._interval_seconds)

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())
        logger.info("scheduler_started", extra={"interval_seconds": self._interval_seconds})

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            logger.info("scheduler_stopped")
