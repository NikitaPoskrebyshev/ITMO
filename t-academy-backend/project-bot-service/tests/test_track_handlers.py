from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bot.handlers import (
    CANCELLED_MESSAGE,
    HELP_MESSAGE,
    LIST_EMPTY,
    LIST_HEADER,
    NOTHING_TO_CANCEL,
    TRACK_ASK_TAGS,
    TRACK_ASK_URL,
    TRACK_DUPLICATE,
    TRACK_INVALID_URL,
    TRACK_SCRAPPER_ERROR,
    TRACK_SUCCESS,
    UNTRACK_ASK_URL,
    UNTRACK_NOT_FOUND,
    UNTRACK_SUCCESS,
    BotHandlers,
)
from bot.models import LinkResponse, ListLinksResponse
from bot.repositories import InMemoryTrackStateRepository, InMemoryUserRepository, TrackDialogState
from bot.scrapper_client import (
    DuplicateLinkError,
    LinkNotFoundError,
    ScrapperError,
)


class FakeMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


class FakeUser:
    def __init__(self, user_id: int = 1, username: str = "tester") -> None:
        self.id = user_id
        self.username = username


class FakeChat:
    def __init__(self, chat_id: int = 100) -> None:
        self.id = chat_id


class FakeUpdate:
    def __init__(self, text: str, chat_id: int = 100, user_id: int = 1) -> None:
        self.effective_message = FakeMessage(text)
        self.effective_user = FakeUser(user_id)
        self.effective_chat = FakeChat(chat_id)


def make_handlers(scrapper_client=None) -> BotHandlers:
    if scrapper_client is None:
        scrapper_client = AsyncMock()
    return BotHandlers(
        user_repository=InMemoryUserRepository(),
        track_state_repository=InMemoryTrackStateRepository(),
        scrapper_client=scrapper_client,
    )


# ---- /track dialog ----


@pytest.mark.asyncio
async def test_track_starts_dialog() -> None:
    handlers = make_handlers()
    update = FakeUpdate("/track")

    await handlers.track(update, None)

    assert update.effective_message.replies == [TRACK_ASK_URL]
    session = handlers.track_state_repository.get_session(100)
    assert session.state == TrackDialogState.WAITING_FOR_TRACK_URL


@pytest.mark.asyncio
async def test_track_invalid_url_shows_error() -> None:
    handlers = make_handlers()
    await handlers.track(FakeUpdate("/track"), None)

    update = FakeUpdate("not-a-url")
    await handlers.handle_text(update, None)

    assert update.effective_message.replies == [TRACK_INVALID_URL]
    session = handlers.track_state_repository.get_session(100)
    assert session.state == TrackDialogState.WAITING_FOR_TRACK_URL


@pytest.mark.asyncio
async def test_track_valid_url_asks_for_tags() -> None:
    handlers = make_handlers()
    await handlers.track(FakeUpdate("/track"), None)

    update = FakeUpdate("https://github.com/owner/repo")
    await handlers.handle_text(update, None)

    assert update.effective_message.replies == [TRACK_ASK_TAGS]
    session = handlers.track_state_repository.get_session(100)
    assert session.state == TrackDialogState.WAITING_FOR_TRACK_TAGS
    assert session.pending_url == "https://github.com/owner/repo"


@pytest.mark.asyncio
async def test_track_happy_path_with_tags() -> None:
    scrapper = AsyncMock()
    scrapper.add_link.return_value = LinkResponse(
        id=1, url="https://github.com/owner/repo", tags=["python", "bot"]
    )
    handlers = make_handlers(scrapper)

    await handlers.track(FakeUpdate("/track"), None)
    await handlers.handle_text(FakeUpdate("https://github.com/owner/repo"), None)
    update = FakeUpdate("python, bot")
    await handlers.handle_text(update, None)

    assert TRACK_SUCCESS.format(url="https://github.com/owner/repo") in update.effective_message.replies
    session = handlers.track_state_repository.get_session(100)
    assert session.state == TrackDialogState.IDLE


@pytest.mark.asyncio
async def test_track_happy_path_empty_tags() -> None:
    scrapper = AsyncMock()
    scrapper.add_link.return_value = LinkResponse(
        id=1, url="https://github.com/owner/repo", tags=[]
    )
    handlers = make_handlers(scrapper)

    await handlers.track(FakeUpdate("/track"), None)
    await handlers.handle_text(FakeUpdate("https://github.com/owner/repo"), None)
    update = FakeUpdate("")
    await handlers.handle_text(update, None)

    assert TRACK_SUCCESS.format(url="https://github.com/owner/repo") in update.effective_message.replies
    scrapper.add_link.assert_awaited_once()
    call_args = scrapper.add_link.call_args
    assert call_args.args[1].tags == []


@pytest.mark.asyncio
async def test_track_duplicate_link() -> None:
    scrapper = AsyncMock()
    scrapper.add_link.side_effect = DuplicateLinkError(400, "Link already tracked")
    handlers = make_handlers(scrapper)

    await handlers.track(FakeUpdate("/track"), None)
    await handlers.handle_text(FakeUpdate("https://github.com/owner/repo"), None)
    update = FakeUpdate("tag1")
    await handlers.handle_text(update, None)

    assert TRACK_DUPLICATE in update.effective_message.replies


@pytest.mark.asyncio
async def test_track_scrapper_error() -> None:
    scrapper = AsyncMock()
    scrapper.add_link.side_effect = ScrapperError(500, "Internal error")
    handlers = make_handlers(scrapper)

    await handlers.track(FakeUpdate("/track"), None)
    await handlers.handle_text(FakeUpdate("https://github.com/owner/repo"), None)
    update = FakeUpdate("tag1")
    await handlers.handle_text(update, None)

    assert TRACK_SCRAPPER_ERROR in update.effective_message.replies


# ---- /cancel ----


@pytest.mark.asyncio
async def test_cancel_during_track_clears_state() -> None:
    handlers = make_handlers()
    await handlers.track(FakeUpdate("/track"), None)

    update = FakeUpdate("/cancel")
    await handlers.cancel(update, None)

    assert update.effective_message.replies == [CANCELLED_MESSAGE]
    session = handlers.track_state_repository.get_session(100)
    assert session.state == TrackDialogState.IDLE


@pytest.mark.asyncio
async def test_cancel_when_idle_says_nothing_to_cancel() -> None:
    handlers = make_handlers()
    update = FakeUpdate("/cancel")
    await handlers.cancel(update, None)

    assert update.effective_message.replies == [NOTHING_TO_CANCEL]


@pytest.mark.asyncio
async def test_other_command_during_track_cancels_dialog() -> None:
    handlers = make_handlers()
    await handlers.track(FakeUpdate("/track"), None)

    update = FakeUpdate("/help")
    await handlers.help_command(update, None)

    assert update.effective_message.replies == [HELP_MESSAGE]
    session = handlers.track_state_repository.get_session(100)
    assert session.state == TrackDialogState.IDLE


# ---- /untrack ----


@pytest.mark.asyncio
async def test_untrack_starts_dialog() -> None:
    handlers = make_handlers()
    update = FakeUpdate("/untrack")
    await handlers.untrack(update, None)

    assert update.effective_message.replies == [UNTRACK_ASK_URL]
    session = handlers.track_state_repository.get_session(100)
    assert session.state == TrackDialogState.WAITING_FOR_UNTRACK_URL


@pytest.mark.asyncio
async def test_untrack_happy_path() -> None:
    scrapper = AsyncMock()
    scrapper.remove_link.return_value = LinkResponse(
        id=1, url="https://github.com/owner/repo", tags=[]
    )
    handlers = make_handlers(scrapper)

    await handlers.untrack(FakeUpdate("/untrack"), None)
    update = FakeUpdate("https://github.com/owner/repo")
    await handlers.handle_text(update, None)

    assert UNTRACK_SUCCESS.format(url="https://github.com/owner/repo") in update.effective_message.replies
    session = handlers.track_state_repository.get_session(100)
    assert session.state == TrackDialogState.IDLE


@pytest.mark.asyncio
async def test_untrack_not_found() -> None:
    scrapper = AsyncMock()
    scrapper.remove_link.side_effect = LinkNotFoundError(404, "Link not found")
    handlers = make_handlers(scrapper)

    await handlers.untrack(FakeUpdate("/untrack"), None)
    update = FakeUpdate("https://github.com/owner/repo")
    await handlers.handle_text(update, None)

    assert UNTRACK_NOT_FOUND in update.effective_message.replies


# ---- /list ----


@pytest.mark.asyncio
async def test_list_when_empty() -> None:
    scrapper = AsyncMock()
    scrapper.list_links.return_value = ListLinksResponse(links=[], size=0)
    handlers = make_handlers(scrapper)

    update = FakeUpdate("/list")
    await handlers.list_links(update, None)

    assert update.effective_message.replies == [LIST_EMPTY]


@pytest.mark.asyncio
async def test_list_when_non_empty() -> None:
    scrapper = AsyncMock()
    scrapper.list_links.return_value = ListLinksResponse(
        links=[
            LinkResponse(id=1, url="https://github.com/a/b", tags=["tag1"]),
            LinkResponse(id=2, url="https://stackoverflow.com/questions/1", tags=[]),
        ],
        size=2,
    )
    handlers = make_handlers(scrapper)

    update = FakeUpdate("/list")
    await handlers.list_links(update, None)

    reply = update.effective_message.replies[0]
    assert LIST_HEADER in reply
    assert "https://github.com/a/b" in reply
    assert "https://stackoverflow.com/questions/1" in reply
    assert "tag1" in reply
