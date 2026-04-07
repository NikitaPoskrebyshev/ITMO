from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from bot.handlers import BotHandlers
from bot.repositories import InMemoryTrackStateRepository, InMemoryUserRepository
from bot.scrapper_client import ScrapperHttpClient
from bot.web_server import UpdatesServer

if TYPE_CHECKING:
    from telegram.ext import Application


class BotApplication:
    def __init__(
        self,
        token: str,
        polling_timeout_seconds: int,
        scrapper_base_url: str = "http://localhost:8080",
        scrapper_timeout_seconds: int = 10,
        server_host: str = "0.0.0.0",
        server_port: int = 8081,
    ) -> None:
        self._token = token
        self._polling_timeout_seconds = polling_timeout_seconds
        self._scrapper_base_url = scrapper_base_url
        self._scrapper_timeout_seconds = scrapper_timeout_seconds
        self._server_host = server_host
        self._server_port = server_port

        self._user_repository = InMemoryUserRepository()
        self._track_state_repository = InMemoryTrackStateRepository()
        self._scrapper_client = ScrapperHttpClient(
            base_url=scrapper_base_url,
            timeout_seconds=scrapper_timeout_seconds,
        )
        self._handlers = BotHandlers(
            user_repository=self._user_repository,
            track_state_repository=self._track_state_repository,
            scrapper_client=self._scrapper_client,
        )

    def build(self) -> Application:
        from telegram.ext import (
            ApplicationBuilder,
            CommandHandler,
            MessageHandler,
            filters,
        )

        server_host = self._server_host
        server_port = self._server_port

        async def post_init(application: Application) -> None:
            server = UpdatesServer(
                host=server_host,
                port=server_port,
                bot=application.bot,
            )
            asyncio.ensure_future(server.serve())

        application = ApplicationBuilder().token(self._token).post_init(post_init).build()

        application.add_handler(CommandHandler("start", self._handlers.start))
        application.add_handler(CommandHandler("help", self._handlers.help_command))
        application.add_handler(CommandHandler("track", self._handlers.track))
        application.add_handler(CommandHandler("untrack", self._handlers.untrack))
        application.add_handler(CommandHandler("list", self._handlers.list_links))
        application.add_handler(CommandHandler("cancel", self._handlers.cancel))
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self._handlers.handle_text,
            )
        )
        application.add_handler(
            MessageHandler(filters.COMMAND, self._handlers.unknown_command)
        )
        return application

    def run(self) -> None:
        application = self.build()
        application.run_polling(timeout=self._polling_timeout_seconds)
