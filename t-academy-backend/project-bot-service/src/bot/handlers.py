from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from bot.models import AddLinkRequest, RemoveLinkRequest
from bot.repositories import InMemoryTrackStateRepository, InMemoryUserRepository, TrackDialogState, TrackSession
from bot.scrapper_client import (
    ChatNotFoundError,
    DuplicateLinkError,
    InvalidLinkError,
    LinkNotFoundError,
    ScrapperClient,
    ScrapperError,
)

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
    "/track — добавить ссылку для отслеживания\n"
    "/untrack — удалить ссылку из отслеживания\n"
    "/list — показать все отслеживаемые ссылки\n"
    "/cancel — отменить текущее действие"
)
UNKNOWN_COMMAND_MESSAGE = "Неизвестная команда. Воспользуйтесь /help, чтобы посмотреть список доступных команд."

TRACK_ASK_URL = "Введите ссылку для отслеживания:"
TRACK_ASK_TAGS = "Введите теги через запятую или отправьте пустое сообщение, чтобы пропустить:"
TRACK_SUCCESS = "Ссылка добавлена: {url}"
TRACK_DUPLICATE = "Ссылка уже отслеживается"
TRACK_INVALID_URL = "Некорректный формат ссылки. Введите URL, начинающийся с http:// или https://"
TRACK_SCRAPPER_ERROR = "Не удалось добавить ссылку. Попробуйте позже."

UNTRACK_ASK_URL = "Введите ссылку для удаления из отслеживания:"
UNTRACK_SUCCESS = "Ссылка удалена: {url}"
UNTRACK_NOT_FOUND = "Ссылка не найдена."
UNTRACK_SCRAPPER_ERROR = "Не удалось удалить ссылку. Попробуйте позже."

LIST_EMPTY = "Нет отслеживаемых ссылок."
LIST_HEADER = "Отслеживаемые ссылки:\n"
LIST_SCRAPPER_ERROR = "Не удалось получить список ссылок. Попробуйте позже."

CANCELLED_MESSAGE = "Действие отменено."
NOTHING_TO_CANCEL = "Нет активного действия для отмены."


def _is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


@dataclass(slots=True)
class BotHandlers:
    user_repository: InMemoryUserRepository
    track_state_repository: InMemoryTrackStateRepository
    scrapper_client: ScrapperClient

    @staticmethod
    def _extract_payload(
        update: Update,
    ) -> tuple[Message | None, User | None, Chat | None]:
        return update.effective_message, update.effective_user, update.effective_chat

    @staticmethod
    def _log_context(user, chat) -> dict:
        return {
            "chat_id": chat.id if chat is not None else "",
            "user_id": user.id if user is not None else "",
            "username": user.username if user is not None and user.username else "",
        }

    def _clear_dialog(self, chat_id: int) -> None:
        self.track_state_repository.clear_session(chat_id)

    async def start(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        message, user, chat = self._extract_payload(update)

        if message is None or user is None or chat is None:
            logger.info(
                "Start command skipped",
                extra={"event": "start_skipped_missing_payload"},
            )
            return

        self._clear_dialog(chat.id)
        self.user_repository.save_started(user.id)

        try:
            await self.scrapper_client.register_chat(chat.id)
        except Exception:
            logger.exception(
                "Failed to register chat with scrapper",
                extra={"event": "scrapper_register_failed", **self._log_context(user, chat)},
            )

        await message.reply_text(START_MESSAGE)

        logger.info(
            "Start command handled",
            extra={
                "event": "start_command_handled",
                **self._log_context(user, chat),
            },
        )

    async def help_command(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)

        if message is None or user is None or chat is None:
            logger.info(
                "Help command skipped", extra={"event": "help_skipped_missing_payload"}
            )
            return

        self._clear_dialog(chat.id)
        await message.reply_text(HELP_MESSAGE)

        logger.info(
            "Help command handled",
            extra={
                "event": "help_command_handled",
                **self._log_context(user, chat),
            },
        )

    async def track(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        message, user, chat = self._extract_payload(update)

        if message is None or user is None or chat is None:
            logger.info(
                "Track command skipped",
                extra={"event": "track_skipped_missing_payload"},
            )
            return

        self._clear_dialog(chat.id)
        self.track_state_repository.set_session(
            chat.id,
            TrackSession(state=TrackDialogState.WAITING_FOR_TRACK_URL),
        )
        await message.reply_text(TRACK_ASK_URL)

        logger.info(
            "Track dialog started",
            extra={"event": "track_started", **self._log_context(user, chat)},
        )

    async def untrack(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)

        if message is None or user is None or chat is None:
            logger.info(
                "Untrack command skipped",
                extra={"event": "untrack_skipped_missing_payload"},
            )
            return

        self._clear_dialog(chat.id)
        self.track_state_repository.set_session(
            chat.id,
            TrackSession(state=TrackDialogState.WAITING_FOR_UNTRACK_URL),
        )
        await message.reply_text(UNTRACK_ASK_URL)

        logger.info(
            "Untrack dialog started",
            extra={"event": "untrack_started", **self._log_context(user, chat)},
        )

    async def list_links(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)

        if message is None or user is None or chat is None:
            logger.info(
                "List command skipped",
                extra={"event": "list_skipped_missing_payload"},
            )
            return

        self._clear_dialog(chat.id)

        try:
            result = await self.scrapper_client.list_links(chat.id)
        except Exception:
            logger.exception(
                "Failed to fetch links from scrapper",
                extra={"event": "scrapper_request_failed", **self._log_context(user, chat)},
            )
            await message.reply_text(LIST_SCRAPPER_ERROR)
            return

        if not result.links:
            await message.reply_text(LIST_EMPTY)
            logger.info(
                "List command handled (empty)",
                extra={"event": "list_command_handled", **self._log_context(user, chat), "count": 0},
            )
            return

        lines = [LIST_HEADER]
        for link in result.links:
            tags_str = ", ".join(link.tags) if link.tags else "—"
            lines.append(f"• {link.url} [{tags_str}]")
        await message.reply_text("\n".join(lines))

        logger.info(
            "List command handled",
            extra={
                "event": "list_command_handled",
                **self._log_context(user, chat),
                "count": result.size,
            },
        )

    async def cancel(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)

        if message is None or user is None or chat is None:
            logger.info(
                "Cancel command skipped",
                extra={"event": "cancel_skipped_missing_payload"},
            )
            return

        session = self.track_state_repository.get_session(chat.id)
        if session.state == TrackDialogState.IDLE:
            await message.reply_text(NOTHING_TO_CANCEL)
        else:
            self._clear_dialog(chat.id)
            await message.reply_text(CANCELLED_MESSAGE)
            logger.info(
                "Dialog cancelled",
                extra={"event": "track_cancelled", **self._log_context(user, chat)},
            )

    async def handle_text(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)

        if message is None or user is None or chat is None:
            return

        session = self.track_state_repository.get_session(chat.id)

        if session.state == TrackDialogState.WAITING_FOR_TRACK_URL:
            await self._handle_track_url(message, user, chat, session)
        elif session.state == TrackDialogState.WAITING_FOR_TRACK_TAGS:
            await self._handle_track_tags(message, user, chat, session)
        elif session.state == TrackDialogState.WAITING_FOR_UNTRACK_URL:
            await self._handle_untrack_url(message, user, chat, session)

    async def _handle_track_url(self, message, user, chat, _session) -> None:
        url = (message.text or "").strip()
        logger.info(
            "Track URL received",
            extra={"event": "track_link_received", **self._log_context(user, chat), "url": url},
        )

        if not _is_valid_url(url):
            await message.reply_text(TRACK_INVALID_URL)
            return

        self.track_state_repository.set_session(
            chat.id,
            TrackSession(
                state=TrackDialogState.WAITING_FOR_TRACK_TAGS,
                pending_url=url,
            ),
        )
        await message.reply_text(TRACK_ASK_TAGS)

    async def _handle_track_tags(self, message, user, chat, session) -> None:
        raw = (message.text or "").strip()
        tags = [t.strip() for t in raw.split(",") if t.strip()] if raw else []
        url = session.pending_url or ""

        self._clear_dialog(chat.id)

        try:
            result = await self.scrapper_client.add_link(
                chat.id, AddLinkRequest(link=url, tags=tags)
            )
        except DuplicateLinkError:
            await message.reply_text(TRACK_DUPLICATE)
            logger.info(
                "Duplicate link detected",
                extra={"event": "track_duplicate_link", **self._log_context(user, chat), "url": url},
            )
            return
        except (InvalidLinkError, ChatNotFoundError, ScrapperError):
            logger.exception(
                "Scrapper error while adding link",
                extra={"event": "scrapper_request_failed", **self._log_context(user, chat), "url": url},
            )
            await message.reply_text(TRACK_SCRAPPER_ERROR)
            return

        await message.reply_text(TRACK_SUCCESS.format(url=result.url))
        logger.info(
            "Track completed",
            extra={"event": "track_completed", **self._log_context(user, chat), "url": url},
        )

    async def _handle_untrack_url(self, message, user, chat, _session) -> None:
        url = (message.text or "").strip()
        self._clear_dialog(chat.id)

        if not _is_valid_url(url):
            await message.reply_text(TRACK_INVALID_URL)
            return

        try:
            result = await self.scrapper_client.remove_link(
                chat.id, RemoveLinkRequest(link=url)
            )
        except (LinkNotFoundError, ChatNotFoundError):
            await message.reply_text(UNTRACK_NOT_FOUND)
            logger.info(
                "Link not found for untrack",
                extra={"event": "untrack_not_found", **self._log_context(user, chat), "url": url},
            )
            return
        except ScrapperError:
            logger.exception(
                "Scrapper error while removing link",
                extra={"event": "scrapper_request_failed", **self._log_context(user, chat), "url": url},
            )
            await message.reply_text(UNTRACK_SCRAPPER_ERROR)
            return

        await message.reply_text(UNTRACK_SUCCESS.format(url=result.url))
        logger.info(
            "Untrack completed",
            extra={"event": "untrack_completed", **self._log_context(user, chat), "url": url},
        )

    async def unknown_command(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message, user, chat = self._extract_payload(update)

        if message is None or user is None or chat is None:
            logger.info(
                "Unknown command skipped",
                extra={"event": "unknown_skipped_missing_payload"},
            )
            return

        self._clear_dialog(chat.id)
        await message.reply_text(UNKNOWN_COMMAND_MESSAGE)

        logger.info(
            "Unknown command handled",
            extra={
                "event": "unknown_command_handled",
                **self._log_context(user, chat),
                "text": message.text or "",
            },
        )
