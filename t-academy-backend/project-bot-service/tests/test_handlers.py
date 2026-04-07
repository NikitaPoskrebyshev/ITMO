from unittest.mock import AsyncMock

import pytest

from bot.handlers import (
    HELP_MESSAGE,
    START_MESSAGE,
    UNKNOWN_COMMAND_MESSAGE,
    BotHandlers,
)
from bot.repositories import InMemoryTrackStateRepository, InMemoryUserRepository


def test_repository_tracks_started_users() -> None:
    repo = InMemoryUserRepository()

    assert repo.is_started(228) is False
    repo.save_started(228)
    assert repo.is_started(228) is True


def test_repository_does_not_confuse_users() -> None:
    repo = InMemoryUserRepository()
    repo.save_started(1)

    assert repo.is_started(2) is False


class FakeMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


class FakeUser:
    def __init__(self, user_id: int, username: str) -> None:
        self.id = user_id
        self.username = username


class FakeChat:
    def __init__(self, chat_id: int) -> None:
        self.id = chat_id


class FakeUpdate:
    def __init__(self, text: str) -> None:
        self.effective_message = FakeMessage(text)
        self.effective_user = FakeUser(1, "tester")
        self.effective_chat = FakeChat(100)


def make_handlers(user_repository=None) -> BotHandlers:
    return BotHandlers(
        user_repository=user_repository or InMemoryUserRepository(),
        track_state_repository=InMemoryTrackStateRepository(),
        scrapper_client=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_start_command_returns_greeting() -> None:
    repository = InMemoryUserRepository()
    handlers = make_handlers(repository)
    update = FakeUpdate("/start")

    await handlers.start(update, None)

    assert update.effective_message.replies == [START_MESSAGE]
    assert repository.is_started(1) is True


@pytest.mark.asyncio
async def test_help_command_returns_command_description() -> None:
    handlers = make_handlers()
    update = FakeUpdate("/help")

    await handlers.help_command(update, None)

    assert update.effective_message.replies == [HELP_MESSAGE]


@pytest.mark.asyncio
async def test_unknown_command_returns_error_message() -> None:
    handlers = make_handlers()
    update = FakeUpdate("/unknown")

    await handlers.unknown_command(update, None)

    assert update.effective_message.replies == [UNKNOWN_COMMAND_MESSAGE]
