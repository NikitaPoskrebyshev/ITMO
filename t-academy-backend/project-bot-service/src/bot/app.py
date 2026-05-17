from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import uvicorn

from .clients import ScrapperHttpClient
from .handlers import BotHandlers
from .http_server import create_updates_app
from .models import LinkUpdate
from .repositories import InMemoryUserRepository, run_migrations
from .state import InMemoryStateRepository

if TYPE_CHECKING:
    from telegram.ext import Application


logger = logging.getLogger(__name__)


class BotApplication:
    def __init__(
        self,
        token: str,
        polling_timeout_seconds: int,
        scrapper_base_url: str = "http://localhost:8080",
        scrapper_timeout_seconds: int = 10,
        server_host: str = "0.0.0.0",
        server_port: int = 8081,
        db_dsn: str = "postgresql://bot:bot@localhost:5432/bot",
        db_access_type: str = "SQL",
        notification_transport: str = "http",
        kafka_bootstrap_servers: str = "localhost:9094",
        kafka_topic: str = "link-updates",
        kafka_group_id: str = "bot-service",
    ) -> None:
        self._token = token
        self._polling_timeout_seconds = polling_timeout_seconds
        self._user_repository = InMemoryUserRepository()
        self._state_repository = InMemoryStateRepository()
        self._scrapper_client = ScrapperHttpClient(
            base_url=scrapper_base_url,
            timeout_seconds=scrapper_timeout_seconds,
        )
        self._handlers = BotHandlers(
            user_repository=self._user_repository,
            scrapper_client=self._scrapper_client,
            state_repository=self._state_repository,
        )
        self._server_host = server_host
        self._server_port = server_port
        self._db_dsn = db_dsn
        self._db_access_type = db_access_type.upper()
        self._notification_transport = notification_transport
        self._kafka_bootstrap_servers = kafka_bootstrap_servers
        self._kafka_topic = kafka_topic
        self._kafka_group_id = kafka_group_id

    def build(self) -> Application:
        from telegram.ext import (
            ApplicationBuilder,
            CommandHandler,
            MessageHandler,
            filters,
        )

        application = ApplicationBuilder().token(self._token).build()
        application.add_handler(CommandHandler("start", self._handlers.start))
        application.add_handler(CommandHandler("help", self._handlers.help_command))
        application.add_handler(CommandHandler("cancel", self._handlers.cancel))
        application.add_handler(CommandHandler("track", self._handlers.track))
        application.add_handler(CommandHandler("untrack", self._handlers.untrack))
        application.add_handler(CommandHandler("list", self._handlers.list_links))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handlers.handle_text)
        )
        application.add_handler(
            MessageHandler(filters.COMMAND, self._handlers.unknown_command)
        )
        return application

    async def _on_update(self, update: LinkUpdate) -> None:
        from telegram import Bot

        bot = Bot(token=self._token)
        text = f"Обновление по ссылке:\n{update.url}\n\n{update.description}"
        for chat_id in update.tg_chat_ids:
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception as exc:
                logger.warning(
                    "send_update_failed",
                    extra={
                        "event": "send_update_failed",
                        "chat_id": chat_id,
                        "error": str(exc),
                    },
                )

    async def _create_chat_repository(self):
        await run_migrations(self._db_dsn)

        if self._db_access_type == "ORM":
            from .repositories_orm import (
                OrmChatRepository,
                create_orm_engine,
                create_orm_session_factory,
            )

            engine = create_orm_engine(self._db_dsn)
            session_factory = create_orm_session_factory(engine)
            return OrmChatRepository(session_factory)
        else:
            from .repositories_sql import SqlChatRepository, create_sql_pool

            pool = await create_sql_pool(self._db_dsn)
            return SqlChatRepository(pool)

    def run(self) -> None:
        asyncio.run(self._run_async())

    async def _run_async(self) -> None:
        await self._create_chat_repository()
        logger.info(
            "db_initialized",
            extra={"event": "db_initialized", "access_type": self._db_access_type},
        )

        application = self.build()
        fastapi_app = create_updates_app(self._on_update)

        config = uvicorn.Config(
            fastapi_app,
            host=self._server_host,
            port=self._server_port,
            log_level="error",
        )
        http_server = uvicorn.Server(config)

        kafka_consumer = None
        if self._notification_transport == "kafka":
            from .kafka_consumer import KafkaUpdateConsumer

            kafka_consumer = KafkaUpdateConsumer(
                bootstrap_servers=self._kafka_bootstrap_servers,
                topic=self._kafka_topic,
                group_id=self._kafka_group_id,
                on_update=self._on_update,
            )
            await kafka_consumer.start()
            logger.info(
                "kafka_consumer_started",
                extra={
                    "event": "kafka_consumer_started",
                    "topic": self._kafka_topic,
                    "bootstrap_servers": self._kafka_bootstrap_servers,
                },
            )

        async with application:
            await application.start()
            assert application.updater is not None
            await application.updater.start_polling(drop_pending_updates=True)
            logger.info(
                "bot_started",
                extra={"event": "bot_started", "server_port": self._server_port},
            )

            try:
                await http_server.serve()
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass
            finally:
                await application.updater.stop()
                await application.stop()
                if kafka_consumer is not None:
                    await kafka_consumer.stop()
