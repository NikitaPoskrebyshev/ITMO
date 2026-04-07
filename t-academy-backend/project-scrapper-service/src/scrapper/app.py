from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .clients.bot_client import BotClient
from .clients.github_client import GitHubClient
from .clients.stackoverflow_client import StackOverflowClient
from .config.config import AppConfig
from .handlers.chat_handlers import create_chat_router
from .handlers.link_handlers import create_link_router
from .repositories.repository import InMemoryRepository
from .scheduler.scheduler import Scheduler
from .services.chat_service import ChatService
from .services.link_service import LinkService


def create_app(config: AppConfig) -> FastAPI:
    repository = InMemoryRepository()
    chat_service = ChatService(repository)
    link_service = LinkService(repository)

    github_client = GitHubClient(timeout_seconds=config.http.timeout_seconds)
    stackoverflow_client = StackOverflowClient(timeout_seconds=config.http.timeout_seconds)
    bot_client = BotClient(
        base_url=config.bot_service.base_url,
        timeout_seconds=config.http.timeout_seconds,
    )
    scheduler = Scheduler(
        repository=repository,
        github_client=github_client,
        stackoverflow_client=stackoverflow_client,
        bot_client=bot_client,
        interval_seconds=config.scheduler.interval_seconds,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        scheduler.start()
        yield
        scheduler.stop()

    app = FastAPI(title="Scrapper Service", lifespan=lifespan)
    app.include_router(create_chat_router(chat_service))
    app.include_router(create_link_router(link_service))
    return app
