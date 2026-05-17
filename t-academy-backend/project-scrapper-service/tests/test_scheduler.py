from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from scrapper.clients.github_client import GitHubClient
from scrapper.clients.message_sender import MessageSender
from scrapper.clients.stackoverflow_client import StackOverflowClient
from scrapper.models.models import UpdateInfo
from scrapper.repositories.in_memory import InMemoryRepository
from scrapper.scheduler.scheduler import Scheduler

GITHUB_URL = "https://github.com/octocat/Hello-World"
SO_URL = "https://stackoverflow.com/questions/11227809/why-is-sorted-faster"

_UPDATE = UpdateInfo(
    update_type="issue",
    title="[Issue #1] Bug",
    author="octocat",
    created_at="2024-02-01 12:00 UTC",
    preview="Some preview",
    new_timestamp="2024-02-01T12:00:00Z",
)


@pytest_asyncio.fixture
async def repository() -> InMemoryRepository:
    repo = InMemoryRepository()
    await repo.register_chat(1)
    await repo.add_link(1, GITHUB_URL, "github", [])
    return repo


@pytest.fixture
def github_client() -> MagicMock:
    client = MagicMock(spec=GitHubClient)
    client.get_updates = AsyncMock(return_value=([], None))
    return client


@pytest.fixture
def stackoverflow_client() -> MagicMock:
    client = MagicMock(spec=StackOverflowClient)
    client.get_updates = AsyncMock(return_value=([], None))
    return client


@pytest.fixture
def sender() -> MagicMock:
    s = MagicMock(spec=MessageSender)
    s.send_update = AsyncMock()
    return s


@pytest.fixture
def scheduler(
    repository: InMemoryRepository,
    github_client: MagicMock,
    stackoverflow_client: MagicMock,
    sender: MagicMock,
) -> Scheduler:
    return Scheduler(
        repository=repository,
        github_client=github_client,
        stackoverflow_client=stackoverflow_client,
        sender=sender,
        interval_seconds=60,
        batch_size=100,
    )


async def test_scheduler_detects_update_and_notifies(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    sender: MagicMock,
    github_client: MagicMock,
) -> None:
    github_client.get_updates = AsyncMock(
        return_value=([_UPDATE], "2024-02-01T12:00:00Z")
    )
    link = (await repository.get_all_links())[0]

    await scheduler._check_link(link)

    sender.send_update.assert_called_once()
    assert (await repository.get_all_links())[
        0
    ].last_known_update == "2024-02-01T12:00:00Z"


async def test_scheduler_no_notification_when_no_updates(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    sender: MagicMock,
    github_client: MagicMock,
) -> None:
    github_client.get_updates = AsyncMock(return_value=([], "2024-02-01T12:00:00Z"))
    link = (await repository.get_all_links())[0]

    await scheduler._check_link(link)

    sender.send_update.assert_not_called()


async def test_scheduler_does_not_crash_on_api_failure(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    sender: MagicMock,
    github_client: MagicMock,
) -> None:
    github_client.get_updates = AsyncMock(side_effect=Exception("API down"))
    link = (await repository.get_all_links())[0]

    await scheduler._check_link_safe(link)  # must not raise

    sender.send_update.assert_not_called()


async def test_scheduler_error_in_one_link_does_not_affect_others(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    sender: MagicMock,
    github_client: MagicMock,
) -> None:
    await repository.register_chat(2)
    await repository.add_link(2, SO_URL, "stackoverflow", [])

    call_count = 0

    async def flaky_get_updates(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("first link failed")
        return ([_UPDATE], "2024-02-01T12:00:00Z")

    github_client.get_updates = AsyncMock(side_effect=flaky_get_updates)
    scheduler._stackoverflow_client.get_updates = AsyncMock(
        return_value=([_UPDATE], "2024-02-01T12:00:00Z")
    )

    await scheduler._process_all_links()

    assert sender.send_update.call_count >= 1


async def test_scheduler_sends_correct_chat_ids(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    sender: MagicMock,
    github_client: MagicMock,
) -> None:
    github_client.get_updates = AsyncMock(
        return_value=([_UPDATE], "2024-02-01T12:00:00Z")
    )
    link = (await repository.get_all_links())[0]

    await scheduler._check_link(link)

    sent = sender.send_update.call_args[0][0]
    assert 1 in sent.tg_chat_ids


async def test_scheduler_batch_processing(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    sender: MagicMock,
    github_client: MagicMock,
) -> None:
    github_client.get_updates = AsyncMock(
        return_value=([_UPDATE], "2024-02-01T12:00:00Z")
    )
    scheduler._batch_size = 1

    await repository.register_chat(2)
    await repository.add_link(2, "https://github.com/octocat/Spoon-Knife", "github", [])

    await scheduler._process_all_links()

    assert sender.send_update.call_count == 2


async def test_scheduler_notification_contains_title_and_author(
    scheduler: Scheduler,
    repository: InMemoryRepository,
    sender: MagicMock,
    github_client: MagicMock,
) -> None:
    github_client.get_updates = AsyncMock(
        return_value=([_UPDATE], "2024-02-01T12:00:00Z")
    )
    link = (await repository.get_all_links())[0]

    await scheduler._check_link(link)

    sent = sender.send_update.call_args[0][0]
    assert "[Issue #1] Bug" in sent.description
    assert "octocat" in sent.description
    assert "Some preview" in sent.description
