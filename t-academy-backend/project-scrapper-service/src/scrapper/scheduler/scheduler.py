from __future__ import annotations

import asyncio
import logging

from ..clients.github_client import GitHubClient
from ..clients.message_sender import MessageSender
from ..clients.stackoverflow_client import StackOverflowClient
from ..models.models import LinkUpdate, TrackedLink, UpdateInfo
from ..repositories.repository import ScrapperRepository
from ..services.link_parser import (
    GitHubLink,
    InvalidLinkError,
    StackOverflowLink,
    parse_link,
)

logger = logging.getLogger(__name__)


def _format_description(url: str, update: UpdateInfo) -> str:
    parts = [
        f"Обновление: {url}",
        update.title,
        f"Автор: {update.author}",
        f"Время: {update.created_at}",
    ]
    if update.preview:
        parts.append(f"Превью: {update.preview}")
    return "\n".join(parts)


class Scheduler:
    def __init__(
        self,
        repository: ScrapperRepository,
        github_client: GitHubClient,
        stackoverflow_client: StackOverflowClient,
        sender: MessageSender,
        interval_seconds: int = 60,
        batch_size: int = 100,
    ) -> None:
        self._repository = repository
        self._github_client = github_client
        self._stackoverflow_client = stackoverflow_client
        self._sender = sender
        self._interval_seconds = interval_seconds
        self._batch_size = batch_size
        self._task: asyncio.Task[None] | None = None

    async def _fetch_updates(
        self, link: TrackedLink
    ) -> tuple[list[UpdateInfo], str | None]:
        try:
            parsed = parse_link(link.url)
        except InvalidLinkError:
            return [], None

        if isinstance(parsed, GitHubLink):
            return await self._github_client.get_updates(
                parsed.owner, parsed.repo, link.last_known_update
            )
        if isinstance(parsed, StackOverflowLink):
            return await self._stackoverflow_client.get_updates(
                parsed.question_id, link.last_known_update
            )
        return [], None

    async def _check_link(self, link: TrackedLink) -> None:
        updates, new_timestamp = await self._fetch_updates(link)

        if new_timestamp is None:
            return

        for update in updates:
            logger.info(
                "update_detected", extra={"url": link.url, "type": update.update_type}
            )
            await self._sender.send_update(
                LinkUpdate(
                    id=abs(hash(link.url)),
                    url=link.url,
                    description=_format_description(link.url, update),
                    author=update.author,
                    tg_chat_ids=list(link.chat_ids),
                )
            )

        if new_timestamp != link.last_known_update:
            await self._repository.update_link_state(link.url, new_timestamp)

    async def _check_link_safe(self, link: TrackedLink) -> None:
        try:
            await self._check_link(link)
        except Exception as exc:
            logger.error(
                "link_check_failed",
                extra={"url": link.url, "error": str(exc)},
            )

    async def _process_all_links(self) -> None:
        offset = 0
        while True:
            batch = await self._repository.get_all_links(
                limit=self._batch_size, offset=offset
            )
            if not batch:
                break
            for link in batch:
                await self._check_link_safe(link)
            offset += self._batch_size

    async def _run(self) -> None:
        while True:
            try:
                await self._process_all_links()
            except Exception as exc:
                logger.error("scheduler_error", extra={"error": str(exc)})
            await asyncio.sleep(self._interval_seconds)

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())
        logger.info(
            "scheduler_started", extra={"interval_seconds": self._interval_seconds}
        )

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            logger.info("scheduler_stopped")
