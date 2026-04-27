from __future__ import annotations

import pytest

from bot.clients import LinkAlreadyTrackedError, LinkNotFoundError, ScrapperClientError
from bot.handlers import (
    CANCEL_NO_ACTIVE_MESSAGE,
    HELP_MESSAGE,
    LIST_EMPTY_MESSAGE,
    SCRAPPER_UNAVAILABLE_MESSAGE,
    START_MESSAGE,
    TRACK_ASK_FILTERS_MESSAGE,
    TRACK_ASK_TAGS_MESSAGE,
    TRACK_ASK_URL_MESSAGE,
    TRACK_CANCELLED_MESSAGE,
    TRACK_DUPLICATE_MESSAGE,
    TRACK_INVALID_URL_MESSAGE,
    TRACK_SUCCESS_MESSAGE,
    UNKNOWN_COMMAND_MESSAGE,
    UNTRACK_ASK_URL_MESSAGE,
    UNTRACK_NOT_FOUND_MESSAGE,
    UNTRACK_SUCCESS_MESSAGE,
    BotHandlers,
)
from bot.models import LinkResponse
from bot.repositories import InMemoryUserRepository
from bot.state import InMemoryStateRepository, TrackState


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
    def __init__(self, text: str, user_id: int = 1, chat_id: int = 100) -> None:
        self.effective_message = FakeMessage(text)
        self.effective_user = FakeUser(user_id)
        self.effective_chat = FakeChat(chat_id)


class FakeContext:
    def __init__(self, args: list[str] | None = None) -> None:
        self.args = args or []


class FakeScrapperClient:
    """Configurable fake for ScrapperClient."""

    def __init__(self) -> None:
        self.registered_chats: list[int] = []
        self.added_links: list[tuple[int, str, list[str], list[str]]] = []
        self.removed_links: list[tuple[int, str]] = []
        self.links_to_return: list[LinkResponse] = []
        self.add_link_error: Exception | None = None
        self.remove_link_error: Exception | None = None
        self.list_links_error: Exception | None = None
        self.register_chat_error: Exception | None = None

    async def register_chat(self, chat_id: int) -> None:
        if self.register_chat_error is not None:
            raise self.register_chat_error
        self.registered_chats.append(chat_id)

    async def delete_chat(self, chat_id: int) -> None:
        pass

    async def add_link(
        self, chat_id: int, url: str, tags: list[str], filters: list[str] | None = None
    ) -> LinkResponse:
        if self.add_link_error is not None:
            raise self.add_link_error
        self.added_links.append((chat_id, url, tags, filters or []))
        return LinkResponse(id=1, url=url, tags=tags)

    async def remove_link(self, chat_id: int, url: str) -> LinkResponse:
        if self.remove_link_error is not None:
            raise self.remove_link_error
        self.removed_links.append((chat_id, url))
        return LinkResponse(id=1, url=url, tags=[])

    async def list_links(self, chat_id: int) -> list[LinkResponse]:
        if self.list_links_error is not None:
            raise self.list_links_error
        return list(self.links_to_return)


def make_handlers(
    scrapper: FakeScrapperClient | None = None,
) -> tuple[BotHandlers, InMemoryStateRepository, FakeScrapperClient]:
    state_repo = InMemoryStateRepository()
    client = scrapper or FakeScrapperClient()
    handlers = BotHandlers(
        user_repository=InMemoryUserRepository(),
        scrapper_client=client,
        state_repository=state_repo,
    )
    return handlers, state_repo, client


def test_repository_tracks_started_users() -> None:
    from bot.repositories import InMemoryUserRepository

    repo = InMemoryUserRepository()
    assert repo.is_started(228) is False
    repo.save_started(228)
    assert repo.is_started(228) is True


def test_repository_does_not_confuse_users() -> None:
    from bot.repositories import InMemoryUserRepository

    repo = InMemoryUserRepository()
    repo.save_started(1)
    assert repo.is_started(2) is False


@pytest.mark.asyncio
async def test_start_command_returns_greeting() -> None:
    handlers, _, client = make_handlers()
    update = FakeUpdate("/start")
    await handlers.start(update, None)
    assert update.effective_message.replies == [START_MESSAGE]
    assert 100 in client.registered_chats


@pytest.mark.asyncio
async def test_start_cancels_active_flow() -> None:
    handlers, state_repo, _ = make_handlers()
    state_repo.set_state(100, TrackState.WAITING_FOR_TRACK_URL)

    update = FakeUpdate("/start")
    await handlers.start(update, None)

    assert state_repo.get(100).state == TrackState.IDLE
    assert update.effective_message.replies == [START_MESSAGE]


@pytest.mark.asyncio
async def test_start_still_greets_if_scrapper_unavailable() -> None:
    client = FakeScrapperClient()
    client.register_chat_error = ScrapperClientError("unavailable")
    handlers, _, _ = make_handlers(client)

    update = FakeUpdate("/start")
    await handlers.start(update, None)

    assert update.effective_message.replies == [START_MESSAGE]


@pytest.mark.asyncio
async def test_help_command_returns_description() -> None:
    handlers, _, _ = make_handlers()
    update = FakeUpdate("/help")
    await handlers.help_command(update, None)
    assert update.effective_message.replies == [HELP_MESSAGE]


@pytest.mark.asyncio
async def test_cancel_during_track_flow() -> None:
    handlers, state_repo, _ = make_handlers()
    state_repo.set_state(100, TrackState.WAITING_FOR_TRACK_URL)

    update = FakeUpdate("/cancel")
    await handlers.cancel(update, None)

    assert state_repo.get(100).state == TrackState.IDLE
    assert update.effective_message.replies == [TRACK_CANCELLED_MESSAGE]


@pytest.mark.asyncio
async def test_cancel_when_idle_returns_no_active_message() -> None:
    handlers, _, _ = make_handlers()
    update = FakeUpdate("/cancel")
    await handlers.cancel(update, None)
    assert update.effective_message.replies == [CANCEL_NO_ACTIVE_MESSAGE]


@pytest.mark.asyncio
async def test_track_command_asks_for_url() -> None:
    handlers, state_repo, _ = make_handlers()
    update = FakeUpdate("/track")
    await handlers.track(update, None)
    assert update.effective_message.replies == [TRACK_ASK_URL_MESSAGE]
    assert state_repo.get(100).state == TrackState.WAITING_FOR_TRACK_URL


@pytest.mark.asyncio
async def test_track_valid_url_asks_for_tags() -> None:
    handlers, state_repo, _ = make_handlers()
    state_repo.set_state(100, TrackState.WAITING_FOR_TRACK_URL)

    update = FakeUpdate("https://github.com/user/repo")
    await handlers.handle_text(update, None)

    assert state_repo.get(100).state == TrackState.WAITING_FOR_TRACK_TAGS
    assert state_repo.get(100).pending_url == "https://github.com/user/repo"
    assert update.effective_message.replies == [TRACK_ASK_TAGS_MESSAGE]


@pytest.mark.asyncio
async def test_track_tags_asks_for_filters() -> None:
    handlers, state_repo, _ = make_handlers()
    state_repo.set_state(
        100, TrackState.WAITING_FOR_TRACK_TAGS, pending_url="https://github.com/u/r"
    )

    update = FakeUpdate("python, backend")
    await handlers.handle_text(update, None)

    assert state_repo.get(100).state == TrackState.WAITING_FOR_TRACK_FILTERS
    assert state_repo.get(100).pending_tags == ["python", "backend"]
    assert update.effective_message.replies == [TRACK_ASK_FILTERS_MESSAGE]


@pytest.mark.asyncio
async def test_track_filters_calls_scrapper_and_succeeds() -> None:
    handlers, state_repo, client = make_handlers()
    state_repo.set_state(
        100,
        TrackState.WAITING_FOR_TRACK_FILTERS,
        pending_url="https://github.com/u/r",
        pending_tags=["python", "backend"],
    )

    update = FakeUpdate("bug, docs")
    await handlers.handle_text(update, None)

    assert state_repo.get(100).state == TrackState.IDLE
    assert update.effective_message.replies == [TRACK_SUCCESS_MESSAGE]
    assert client.added_links == [
        (100, "https://github.com/u/r", ["python", "backend"], ["bug", "docs"])
    ]


@pytest.mark.asyncio
async def test_track_empty_filters_adds_link_without_filters() -> None:
    handlers, state_repo, client = make_handlers()
    state_repo.set_state(
        100,
        TrackState.WAITING_FOR_TRACK_FILTERS,
        pending_url="https://github.com/u/r",
        pending_tags=[],
    )

    update = FakeUpdate("")
    await handlers.handle_text(update, None)

    assert update.effective_message.replies == [TRACK_SUCCESS_MESSAGE]
    assert client.added_links[0][2] == []
    assert client.added_links[0][3] == []


@pytest.mark.asyncio
async def test_track_invalid_url_sends_error_and_keeps_state() -> None:
    handlers, state_repo, _ = make_handlers()
    state_repo.set_state(100, TrackState.WAITING_FOR_TRACK_URL)

    update = FakeUpdate("not-a-valid-url")
    await handlers.handle_text(update, None)

    assert state_repo.get(100).state == TrackState.WAITING_FOR_TRACK_URL
    assert update.effective_message.replies == [TRACK_INVALID_URL_MESSAGE]


@pytest.mark.asyncio
async def test_track_non_supported_domain_sends_error() -> None:
    handlers, state_repo, _ = make_handlers()
    state_repo.set_state(100, TrackState.WAITING_FOR_TRACK_URL)

    update = FakeUpdate("https://example.com/something")
    await handlers.handle_text(update, None)

    assert state_repo.get(100).state == TrackState.WAITING_FOR_TRACK_URL
    assert update.effective_message.replies == [TRACK_INVALID_URL_MESSAGE]


@pytest.mark.asyncio
async def test_track_duplicate_link_sends_duplicate_message() -> None:
    client = FakeScrapperClient()
    client.add_link_error = LinkAlreadyTrackedError("already tracked")
    handlers, state_repo, _ = make_handlers(client)
    state_repo.set_state(
        100, TrackState.WAITING_FOR_TRACK_FILTERS, pending_url="https://github.com/u/r"
    )

    update = FakeUpdate("")
    await handlers.handle_text(update, None)

    assert state_repo.get(100).state == TrackState.IDLE
    assert update.effective_message.replies == [TRACK_DUPLICATE_MESSAGE]


@pytest.mark.asyncio
async def test_other_command_during_track_cancels_flow() -> None:
    handlers, state_repo, _ = make_handlers()
    state_repo.set_state(100, TrackState.WAITING_FOR_TRACK_URL)

    update = FakeUpdate("/help")
    await handlers.help_command(update, None)

    assert state_repo.get(100).state == TrackState.IDLE
    assert HELP_MESSAGE in update.effective_message.replies


@pytest.mark.asyncio
async def test_list_empty_sends_empty_message() -> None:
    handlers, _, _ = make_handlers()
    update = FakeUpdate("/list")
    await handlers.list_links(update, None)
    assert update.effective_message.replies == [LIST_EMPTY_MESSAGE]


@pytest.mark.asyncio
async def test_list_non_empty_shows_links() -> None:
    client = FakeScrapperClient()
    client.links_to_return = [
        LinkResponse(id=1, url="https://github.com/user/repo", tags=["python"]),
        LinkResponse(id=2, url="https://stackoverflow.com/questions/123", tags=[]),
    ]
    handlers, _, _ = make_handlers(client)

    update = FakeUpdate("/list")
    await handlers.list_links(update, None)

    reply = update.effective_message.replies[0]
    assert "https://github.com/user/repo" in reply
    assert "https://stackoverflow.com/questions/123" in reply


@pytest.mark.asyncio
async def test_list_with_tag_filter_shows_only_matching_links() -> None:
    client = FakeScrapperClient()
    client.links_to_return = [
        LinkResponse(id=1, url="https://github.com/user/repo", tags=["python"]),
        LinkResponse(
            id=2, url="https://stackoverflow.com/questions/123", tags=["java"]
        ),
    ]
    handlers, _, _ = make_handlers(client)

    update = FakeUpdate("/list python")
    await handlers.list_links(update, FakeContext(args=["python"]))

    reply = update.effective_message.replies[0]
    assert "https://github.com/user/repo" in reply
    assert "https://stackoverflow.com/questions/123" not in reply


@pytest.mark.asyncio
async def test_list_with_tag_filter_no_matches_shows_empty_message() -> None:
    client = FakeScrapperClient()
    client.links_to_return = [
        LinkResponse(id=1, url="https://github.com/user/repo", tags=["python"]),
    ]
    handlers, _, _ = make_handlers(client)

    update = FakeUpdate("/list java")
    await handlers.list_links(update, FakeContext(args=["java"]))

    assert update.effective_message.replies == [LIST_EMPTY_MESSAGE]


@pytest.mark.asyncio
async def test_untrack_asks_for_url() -> None:
    handlers, state_repo, _ = make_handlers()
    update = FakeUpdate("/untrack")
    await handlers.untrack(update, None)
    assert update.effective_message.replies == [UNTRACK_ASK_URL_MESSAGE]
    assert state_repo.get(100).state == TrackState.WAITING_FOR_UNTRACK_URL


@pytest.mark.asyncio
async def test_untrack_removes_link_successfully() -> None:
    handlers, state_repo, client = make_handlers()
    state_repo.set_state(100, TrackState.WAITING_FOR_UNTRACK_URL)

    update = FakeUpdate("https://github.com/user/repo")
    await handlers.handle_text(update, None)

    assert state_repo.get(100).state == TrackState.IDLE
    assert update.effective_message.replies == [UNTRACK_SUCCESS_MESSAGE]
    assert client.removed_links == [(100, "https://github.com/user/repo")]


@pytest.mark.asyncio
async def test_untrack_not_found_sends_error() -> None:
    client = FakeScrapperClient()
    client.remove_link_error = LinkNotFoundError("not found")
    handlers, state_repo, _ = make_handlers(client)
    state_repo.set_state(100, TrackState.WAITING_FOR_UNTRACK_URL)

    update = FakeUpdate("https://github.com/user/repo")
    await handlers.handle_text(update, None)

    assert state_repo.get(100).state == TrackState.IDLE
    assert update.effective_message.replies == [UNTRACK_NOT_FOUND_MESSAGE]


@pytest.mark.asyncio
async def test_scrapper_unavailable_during_track() -> None:
    client = FakeScrapperClient()
    client.register_chat_error = ScrapperClientError("connection refused")
    handlers, state_repo, _ = make_handlers(client)
    state_repo.set_state(
        100, TrackState.WAITING_FOR_TRACK_FILTERS, pending_url="https://github.com/u/r"
    )

    update = FakeUpdate("")
    await handlers.handle_text(update, None)

    assert update.effective_message.replies == [SCRAPPER_UNAVAILABLE_MESSAGE]


@pytest.mark.asyncio
async def test_scrapper_unavailable_during_list() -> None:
    client = FakeScrapperClient()
    client.list_links_error = ScrapperClientError("connection refused")
    handlers, _, _ = make_handlers(client)

    update = FakeUpdate("/list")
    await handlers.list_links(update, None)

    assert update.effective_message.replies == [SCRAPPER_UNAVAILABLE_MESSAGE]


@pytest.mark.asyncio
async def test_unknown_command_returns_error_message() -> None:
    handlers, _, _ = make_handlers()
    update = FakeUpdate("/unknown")
    await handlers.unknown_command(update, None)
    assert update.effective_message.replies == [UNKNOWN_COMMAND_MESSAGE]
