from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .clients import (
    ChatNotFoundError,
    LinkAlreadyTrackedError,
    LinkNotFoundError,
    ScrapperClient,
    ScrapperClientError,
)
from .repositories import InMemoryUserRepository
from .state import InMemoryStateRepository, TrackSession, TrackState

if TYPE_CHECKING:
    from telegram import Chat, Message, Update, User
    from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)

START_MESSAGE = (
    "Добро пожаловать! Используйте /help, чтобы посмотреть доступные команды."
)
HELP_MESSAGE = (
    "Доступные команды:\n"
    "/start — начать работу с ботом\n"
    "/help — показать список доступных команд\n"
    "/track — начать отслеживание ссылки\n"
    "/untrack — прекратить отслеживание ссылки\n"
    "/list — показать отслеживаемые ссылки\n"
    "/cancel — отменить текущее действие"
)
UNKNOWN_COMMAND_MESSAGE = "Неизвестная команда. Воспользуйтесь /help, чтобы посмотреть список доступных команд."

TRACK_ASK_URL_MESSAGE = "Отправьте ссылку для отслеживания:"
TRACK_ASK_TAGS_MESSAGE = "Отправьте теги через запятую (или «skip», чтобы пропустить):"
TRACK_ASK_FILTERS_MESSAGE = (
    "Отправьте фильтры через запятую (или «skip», чтобы пропустить):"
)
TRACK_INVALID_URL_MESSAGE = (
    "Неверный формат ссылки. Поддерживаются ссылки GitHub и StackOverflow."
)
TRACK_DUPLICATE_MESSAGE = "Ссылка уже отслеживается"
TRACK_SUCCESS_MESSAGE = "Ссылка успешно добавлена!"
TRACK_CANCELLED_MESSAGE = "Действие отменено."
CANCEL_NO_ACTIVE_MESSAGE = "Нет активного действия для отмены."

UNTRACK_ASK_URL_MESSAGE = "Отправьте ссылку для прекращения отслеживания:"
UNTRACK_SUCCESS_MESSAGE = "Ссылка успешно удалена!"
UNTRACK_NOT_FOUND_MESSAGE = "Ссылка не найдена."

LIST_EMPTY_MESSAGE = "Вы не отслеживаете ни одной ссылки."
SCRAPPER_UNAVAILABLE_MESSAGE = "Сервис временно недоступен. Попробуйте позже."

_VALID_URL_RE = re.compile(
    r"^https?://(?:www\.)?(?:github\.com/[\w.\-]+/[\w.\-]+|stackoverflow\.com/questions/\d+)",
    re.IGNORECASE,
)


def _is_valid_url(url: str) -> bool:
    return bool(_VALID_URL_RE.match(url.strip()))


def _parse_tags(text: str) -> list[str]:
    if not text.strip() or text.strip().lower() == "skip":
        return []
    return [tag.strip() for tag in text.split(",") if tag.strip()]


@dataclass(slots=True)
class BotHandlers:
    user_repository: InMemoryUserRepository
    scrapper_client: ScrapperClient
    state_repository: InMemoryStateRepository

    @staticmethod
    def _extract_payload(
        update: Update,
    ) -> tuple[Message | None, User | None, Chat | None]:
        return update.effective_message, update.effective_user, update.effective_chat

    @staticmethod
    def _log_context(user: User, chat: Chat) -> dict:
        return {
            "chat_id": chat.id if chat is not None else "",
            "user_id": user.id if user is not None else "",
            "username": user.username if user is not None and user.username else "",
        }

    def _cancel_active_flow(self, chat_id: int) -> bool:
        """Silently reset state if a flow is active. Returns True if something was reset."""
        session = self.state_repository.get(chat_id)
        if session.state != TrackState.IDLE:
            self.state_repository.reset(chat_id)
            return True
        return False

    async def start(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        message, user, chat = self._extract_payload(update)
        if message is None or user is None or chat is None:
            logger.info(
                "start_skipped", extra={"event": "start_skipped_missing_payload"}
            )
            return

        self._cancel_active_flow(chat.id)
        self.user_repository.save_started(user.id)

        try:
            await self.scrapper_client.register_chat(chat.id)
        except ScrapperClientError:
            logger.warning(
                "scrapper_request_failed",
                extra={
                    "event": "scrapper_request_failed",
                    "command": "start",
                    **self._log_context(user, chat),
                },
            )

        await message.reply_text(START_MESSAGE)
        logger.info(
            "start_command_handled",
            extra={"event": "start_command_handled", **self._log_context(user, chat)},
        )

    async def help_command(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)
        if message is None or user is None or chat is None:
            logger.info("help_skipped", extra={"event": "help_skipped_missing_payload"})
            return

        self._cancel_active_flow(chat.id)
        await message.reply_text(HELP_MESSAGE)
        logger.info(
            "help_command_handled",
            extra={"event": "help_command_handled", **self._log_context(user, chat)},
        )

    async def cancel(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        message, user, chat = self._extract_payload(update)
        if message is None or user is None or chat is None:
            return

        was_active = self._cancel_active_flow(chat.id)
        reply = TRACK_CANCELLED_MESSAGE if was_active else CANCEL_NO_ACTIVE_MESSAGE
        await message.reply_text(reply)
        logger.info(
            "track_cancelled" if was_active else "cancel_no_active",
            extra={
                "event": "track_cancelled" if was_active else "cancel_no_active",
                **self._log_context(user, chat),
            },
        )

    async def track(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        message, user, chat = self._extract_payload(update)
        if message is None or user is None or chat is None:
            return

        self._cancel_active_flow(chat.id)
        self.state_repository.set_state(chat.id, TrackState.WAITING_FOR_TRACK_URL)
        await message.reply_text(TRACK_ASK_URL_MESSAGE)
        logger.info(
            "track_started",
            extra={"event": "track_started", **self._log_context(user, chat)},
        )

    async def untrack(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)
        if message is None or user is None or chat is None:
            return

        self._cancel_active_flow(chat.id)
        self.state_repository.set_state(chat.id, TrackState.WAITING_FOR_UNTRACK_URL)
        await message.reply_text(UNTRACK_ASK_URL_MESSAGE)

    async def list_links(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)
        if message is None or user is None or chat is None:
            return

        self._cancel_active_flow(chat.id)

        tag_filter: str | None = None
        if context is not None and getattr(context, "args", None):
            tag_filter = context.args[0]

        try:
            links = await self.scrapper_client.list_links(chat.id)
        except ScrapperClientError:
            logger.warning(
                "scrapper_request_failed",
                extra={
                    "event": "scrapper_request_failed",
                    "command": "list",
                    **self._log_context(user, chat),
                },
            )
            await message.reply_text(SCRAPPER_UNAVAILABLE_MESSAGE)
            return

        if tag_filter:
            links = [link for link in links if tag_filter in link.tags]

        if not links:
            await message.reply_text(LIST_EMPTY_MESSAGE)
            return

        lines = [
            f"• {link.url}" + (f" [{', '.join(link.tags)}]" if link.tags else "")
            for link in links
        ]
        await message.reply_text("Отслеживаемые ссылки:\n" + "\n".join(lines))
        logger.info(
            "list_shown",
            extra={
                "event": "list_shown",
                "count": len(links),
                "tag_filter": tag_filter,
                **self._log_context(user, chat),
            },
        )

    async def handle_text(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)
        if message is None or user is None or chat is None:
            return

        text = message.text or ""
        session = self.state_repository.get(chat.id)

        if session.state == TrackState.WAITING_FOR_TRACK_URL:
            await self._handle_track_url(message, user, chat, text)
        elif session.state == TrackState.WAITING_FOR_TRACK_TAGS:
            await self._handle_track_tags(message, user, chat, text, session)
        elif session.state == TrackState.WAITING_FOR_TRACK_FILTERS:
            await self._handle_track_filters(message, user, chat, text, session)
        elif session.state == TrackState.WAITING_FOR_UNTRACK_URL:
            await self._handle_untrack_url(message, user, chat, text)

    async def _handle_track_url(
        self, message: Message, user: User, chat: Chat, text: str
    ) -> None:
        if not _is_valid_url(text):
            await message.reply_text(TRACK_INVALID_URL_MESSAGE)
            logger.info(
                "track_invalid_url",
                extra={
                    "event": "track_invalid_url",
                    "url": text,
                    **self._log_context(user, chat),
                },
            )
            return

        self.state_repository.set_state(
            chat.id, TrackState.WAITING_FOR_TRACK_TAGS, pending_url=text.strip()
        )
        await message.reply_text(TRACK_ASK_TAGS_MESSAGE)
        logger.info(
            "track_link_received",
            extra={
                "event": "track_link_received",
                "url": text,
                **self._log_context(user, chat),
            },
        )

    async def _handle_track_tags(
        self, message: Message, user: User, chat: Chat, text: str, session: TrackSession
    ) -> None:
        tags = _parse_tags(text)
        self.state_repository.set_state(
            chat.id,
            TrackState.WAITING_FOR_TRACK_FILTERS,
            pending_url=session.pending_url,
            pending_tags=tags,
        )
        await message.reply_text(TRACK_ASK_FILTERS_MESSAGE)
        logger.info(
            "track_tags_received",
            extra={
                "event": "track_tags_received",
                "tags": tags,
                **self._log_context(user, chat),
            },
        )

    async def _handle_track_filters(
        self, message: Message, user: User, chat: Chat, text: str, session: TrackSession
    ) -> None:
        filters = _parse_tags(text)
        url = session.pending_url or ""
        tags = session.pending_tags
        self.state_repository.reset(chat.id)

        try:
            await self.scrapper_client.register_chat(chat.id)
            await self.scrapper_client.add_link(chat.id, url, tags, filters)
            await message.reply_text(TRACK_SUCCESS_MESSAGE)
            logger.info(
                "track_completed",
                extra={
                    "event": "track_completed",
                    "url": url,
                    **self._log_context(user, chat),
                },
            )
        except LinkAlreadyTrackedError:
            await message.reply_text(TRACK_DUPLICATE_MESSAGE)
            logger.info(
                "track_duplicate_link",
                extra={
                    "event": "track_duplicate_link",
                    "url": url,
                    **self._log_context(user, chat),
                },
            )
        except ScrapperClientError:
            logger.warning(
                "scrapper_request_failed",
                extra={
                    "event": "scrapper_request_failed",
                    "url": url,
                    **self._log_context(user, chat),
                },
            )
            await message.reply_text(SCRAPPER_UNAVAILABLE_MESSAGE)

    async def _handle_untrack_url(
        self, message: Message, user: User, chat: Chat, text: str
    ) -> None:
        self.state_repository.reset(chat.id)

        try:
            await self.scrapper_client.remove_link(chat.id, text.strip())
            await message.reply_text(UNTRACK_SUCCESS_MESSAGE)
        except LinkNotFoundError:
            await message.reply_text(UNTRACK_NOT_FOUND_MESSAGE)
        except (ChatNotFoundError, ScrapperClientError):
            logger.warning(
                "scrapper_request_failed",
                extra={
                    "event": "scrapper_request_failed",
                    "url": text,
                    **self._log_context(user, chat),
                },
            )
            await message.reply_text(SCRAPPER_UNAVAILABLE_MESSAGE)

    async def unknown_command(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)
        if message is None or user is None or chat is None:
            logger.info(
                "unknown_skipped", extra={"event": "unknown_skipped_missing_payload"}
            )
            return

        self._cancel_active_flow(chat.id)
        await message.reply_text(UNKNOWN_COMMAND_MESSAGE)
        logger.info(
            "unknown_command_handled",
            extra={
                "event": "unknown_command_handled",
                **self._log_context(user, chat),
                "text": message.text or "",
            },
        )
