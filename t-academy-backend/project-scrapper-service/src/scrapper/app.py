from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .clients.bot_client import BotClient
from .clients.github_client import GitHubClient
from .clients.message_sender import BotHttpSender
from .clients.stackoverflow_client import StackOverflowClient
from .config.config import AppConfig
from .handlers.chat_handlers import create_chat_router
from .handlers.link_handlers import create_link_router
from .models.models import ApiErrorResponse
from .repositories.in_memory import InMemoryRepository
from .repositories.repository import ScrapperRepository, run_migrations
from .scheduler.scheduler import Scheduler
from .services.chat_service import ChatService
from .services.link_service import LinkService

logger = logging.getLogger(__name__)


async def _build_db_repository(
    config: AppConfig,
) -> tuple[ScrapperRepository, Callable]:
    assert config.database is not None
    await run_migrations(config.database.dsn)

    if config.database.access_type == "ORM":
        from .repositories.orm import (
            OrmScrapperRepository,
            create_orm_engine,
            create_orm_session_factory,
        )

        engine = create_orm_engine(config.database.dsn)
        repo: ScrapperRepository = OrmScrapperRepository(
            create_orm_session_factory(engine)
        )

        async def cleanup() -> None:
            await engine.dispose()

        return repo, cleanup
    else:
        from .repositories.sql import SqlScrapperRepository, create_sql_pool

        pool = await create_sql_pool(config.database.dsn)
        repo = SqlScrapperRepository(pool)

        async def cleanup() -> None:  # type: ignore[misc]
            await pool.close()

        return repo, cleanup


async def _noop() -> None:
    pass


def create_app(config: AppConfig) -> FastAPI:
    repository: ScrapperRepository = InMemoryRepository()
    chat_service = ChatService(repository)
    link_service = LinkService(repository)

    github_client = GitHubClient(timeout_seconds=config.http.timeout_seconds)
    stackoverflow_client = StackOverflowClient(
        timeout_seconds=config.http.timeout_seconds
    )
    bot_client = BotClient(
        base_url=config.bot_service.base_url,
        timeout_seconds=config.http.timeout_seconds,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        cleanup = _noop
        active_repo: ScrapperRepository = repository

        if config.database is not None:
            active_repo, cleanup = await _build_db_repository(config)
            chat_service._repository = active_repo  # type: ignore[attr-defined]
            link_service._repository = active_repo  # type: ignore[attr-defined]

        scheduler = Scheduler(
            repository=active_repo,
            github_client=github_client,
            stackoverflow_client=stackoverflow_client,
            sender=BotHttpSender(bot_client),
            interval_seconds=config.scheduler.interval_seconds,
            batch_size=config.scheduler.batch_size,
        )
        scheduler.start()
        yield
        scheduler.stop()
        await cleanup()

    app = FastAPI(title="Scrapper Service", lifespan=lifespan)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        body = ApiErrorResponse(description=str(exc.detail), code=str(exc.status_code))
        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(by_alias=True, exclude_none=True),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        body = ApiErrorResponse(description=str(exc), code="400")
        return JSONResponse(
            status_code=400,
            content=body.model_dump(by_alias=True, exclude_none=True),
        )

    app.include_router(create_chat_router(chat_service))
    app.include_router(create_link_router(link_service))
    return app
