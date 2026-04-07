from unittest.mock import AsyncMock, MagicMock

import pytest

from scrapper.clients.bot_client import BotClient
from scrapper.clients.github_client import GitHubClient
from scrapper.clients.stackoverflow_client import StackOverflowClient
from scrapper.repositories.repository import InMemoryRepository
from scrapper.scheduler.scheduler import Scheduler


@pytest.fixture
def repository() -> InMemoryRepository:
    repo = InMemoryRepository()
    repo.register_chat(1)
    repo.add_link(1, "https://github.com/octocat/Hello-World", "github", [])
    return repo


@pytest.fixture
def github_client() -> MagicMock:
    client = MagicMock(spec=GitHubClient)
    client.get_last_update = AsyncMock(return_value="2024-01-02T00:00:00Z")
    return client


@pytest.fixture
def stackoverflow_client() -> MagicMock:
    client = MagicMock(spec=StackOverflowClient)
    client.get_last_update = AsyncMock(return_value=None)
    return client


@pytest.fixture
def bot_client() -> MagicMock:
    client = MagicMock(spec=BotClient)
    client.send_update = AsyncMock()
    return client


@pytest.fixture
def scheduler(
    repository: InMemoryRepository,
    github_client: MagicMock,
    stackoverflow_client: MagicMock,
    bot_client: MagicMock,
) -> Scheduler:
    return Scheduler(
        repository=repository,
        github_client=github_client,
        stackoverflow_client=stackoverflow_client,
        bot_client=bot_client,
        interval_seconds=60,
    )


async def test_scheduler_detects_update_and_notifies(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    bot_client: MagicMock,
    github_client: MagicMock,
) -> None:
    link = repository.get_all_links()[0]
    link.last_known_update = "2024-01-01T00:00:00Z"
    github_client.get_last_update.return_value = "2024-01-02T00:00:00Z"

    await scheduler._check_link(link)

    bot_client.send_update.assert_called_once()
    assert repository.get_all_links()[0].last_known_update == "2024-01-02T00:00:00Z"


async def test_scheduler_no_notification_when_unchanged(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    bot_client: MagicMock,
    github_client: MagicMock,
) -> None:
    link = repository.get_all_links()[0]
    link.last_known_update = "2024-01-01T00:00:00Z"
    github_client.get_last_update.return_value = "2024-01-01T00:00:00Z"

    await scheduler._check_link(link)

    bot_client.send_update.assert_not_called()


async def test_scheduler_does_not_crash_on_api_failure(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    bot_client: MagicMock,
    github_client: MagicMock,
) -> None:
    github_client.get_last_update.side_effect = Exception("API down")
    link = repository.get_all_links()[0]

    await scheduler._check_link(link)  # must not raise

    bot_client.send_update.assert_not_called()


async def test_scheduler_sends_correct_chat_ids(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    bot_client: MagicMock,
    github_client: MagicMock,
) -> None:
    link = repository.get_all_links()[0]
    link.last_known_update = None
    github_client.get_last_update.return_value = "2024-01-01T00:00:00Z"

    await scheduler._check_link(link)

    sent_update = bot_client.send_update.call_args[0][0]
    assert 1 in sent_update.tg_chat_ids
