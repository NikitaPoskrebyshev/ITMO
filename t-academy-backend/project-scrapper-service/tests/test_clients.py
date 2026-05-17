from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx

from scrapper.clients.bot_client import BotClient
from scrapper.clients.github_client import GitHubClient
from scrapper.clients.stackoverflow_client import StackOverflowClient
from scrapper.models.models import LinkUpdate

GITHUB_ISSUE = {
    "number": 42,
    "title": "Fix login bug",
    "user": {"login": "octocat"},
    "created_at": "2024-02-01T12:00:00Z",
    "body": "A" * 300,
}
GITHUB_PR = {
    "number": 7,
    "title": "Add feature",
    "user": {"login": "dev"},
    "created_at": "2024-02-01T13:00:00Z",
    "body": "New feature",
    "pull_request": {},
}
SO_QUESTION = {
    "items": [{"title": "Why is Python slow?", "last_activity_date": 1706788800}]
}
SO_ANSWER = {
    "items": [
        {
            "owner": {"display_name": "alice"},
            "creation_date": 1706788800,
            "body": "<p>" + "B" * 300 + "</p>",
        }
    ]
}
SO_COMMENT = {
    "items": [
        {
            "owner": {"display_name": "bob"},
            "creation_date": 1706788900,
            "body": "Good point",
        }
    ]
}
SO_EMPTY = {"items": []}


@respx.mock
async def test_github_first_check_returns_no_updates() -> None:
    respx.get("https://api.github.com/repos/octocat/Hello-World/issues").mock(
        return_value=httpx.Response(200, json=[GITHUB_ISSUE])
    )
    updates, ts = await GitHubClient().get_updates("octocat", "Hello-World", since=None)
    assert updates == []
    assert ts == "2024-02-01T12:00:00Z"


@respx.mock
async def test_github_returns_new_issue() -> None:
    respx.get("https://api.github.com/repos/octocat/Hello-World/issues").mock(
        return_value=httpx.Response(200, json=[GITHUB_ISSUE])
    )
    updates, ts = await GitHubClient().get_updates(
        "octocat", "Hello-World", since="2024-01-01T00:00:00Z"
    )
    assert len(updates) == 1
    assert "[Issue #42]" in updates[0].title
    assert updates[0].author == "octocat"
    assert len(updates[0].preview) == 200


@respx.mock
async def test_github_returns_new_pr() -> None:
    respx.get("https://api.github.com/repos/octocat/Hello-World/issues").mock(
        return_value=httpx.Response(200, json=[GITHUB_PR])
    )
    updates, _ = await GitHubClient().get_updates(
        "octocat", "Hello-World", since="2024-01-01T00:00:00Z"
    )
    assert len(updates) == 1
    assert "[PR #7]" in updates[0].title
    assert updates[0].update_type == "pull_request"


@respx.mock
async def test_github_no_new_items_when_since_is_latest() -> None:
    respx.get("https://api.github.com/repos/octocat/Hello-World/issues").mock(
        return_value=httpx.Response(200, json=[GITHUB_ISSUE])
    )
    updates, ts = await GitHubClient().get_updates(
        "octocat", "Hello-World", since="2024-02-01T12:00:00Z"
    )
    assert updates == []
    assert ts == "2024-02-01T12:00:00Z"


@respx.mock
async def test_github_non_2xx_returns_empty() -> None:
    respx.get("https://api.github.com/repos/octocat/Hello-World/issues").mock(
        return_value=httpx.Response(404)
    )
    updates, ts = await GitHubClient().get_updates("octocat", "Hello-World", since=None)
    assert updates == []
    assert ts is None


@respx.mock
async def test_github_preview_truncated_to_200() -> None:
    respx.get("https://api.github.com/repos/octocat/Hello-World/issues").mock(
        return_value=httpx.Response(200, json=[GITHUB_ISSUE])
    )
    updates, _ = await GitHubClient().get_updates(
        "octocat", "Hello-World", since="2024-01-01T00:00:00Z"
    )
    assert len(updates[0].preview) == 200


@respx.mock
async def test_stackoverflow_first_check_returns_no_updates() -> None:
    respx.get("https://api.stackexchange.com/2.3/questions/11227809").mock(
        return_value=httpx.Response(200, json=SO_QUESTION)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/answers").mock(
        return_value=httpx.Response(200, json=SO_ANSWER)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/comments").mock(
        return_value=httpx.Response(200, json=SO_EMPTY)
    )
    updates, ts = await StackOverflowClient().get_updates(11227809, since=None)
    assert updates == []
    assert ts == "1706788800"


@respx.mock
async def test_stackoverflow_returns_new_answer() -> None:
    respx.get("https://api.stackexchange.com/2.3/questions/11227809").mock(
        return_value=httpx.Response(200, json=SO_QUESTION)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/answers").mock(
        return_value=httpx.Response(200, json=SO_ANSWER)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/comments").mock(
        return_value=httpx.Response(200, json=SO_EMPTY)
    )
    updates, _ = await StackOverflowClient().get_updates(11227809, since="1700000000")
    assert len(updates) == 1
    assert updates[0].update_type == "answer"
    assert updates[0].author == "alice"
    assert "Why is Python slow?" in updates[0].title


@respx.mock
async def test_stackoverflow_returns_new_comment() -> None:
    respx.get("https://api.stackexchange.com/2.3/questions/11227809").mock(
        return_value=httpx.Response(200, json=SO_QUESTION)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/answers").mock(
        return_value=httpx.Response(200, json=SO_EMPTY)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/comments").mock(
        return_value=httpx.Response(200, json=SO_COMMENT)
    )
    updates, _ = await StackOverflowClient().get_updates(11227809, since="1700000000")
    assert len(updates) == 1
    assert updates[0].update_type == "comment"
    assert updates[0].author == "bob"


@respx.mock
async def test_stackoverflow_preview_truncated_to_200() -> None:
    respx.get("https://api.stackexchange.com/2.3/questions/11227809").mock(
        return_value=httpx.Response(200, json=SO_QUESTION)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/answers").mock(
        return_value=httpx.Response(200, json=SO_ANSWER)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/comments").mock(
        return_value=httpx.Response(200, json=SO_EMPTY)
    )
    updates, _ = await StackOverflowClient().get_updates(11227809, since="1700000000")
    assert len(updates[0].preview) == 200


@respx.mock
async def test_stackoverflow_html_stripped_from_body() -> None:
    respx.get("https://api.stackexchange.com/2.3/questions/11227809").mock(
        return_value=httpx.Response(200, json=SO_QUESTION)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/answers").mock(
        return_value=httpx.Response(200, json=SO_ANSWER)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/comments").mock(
        return_value=httpx.Response(200, json=SO_EMPTY)
    )
    updates, _ = await StackOverflowClient().get_updates(11227809, since="1700000000")
    assert "<p>" not in updates[0].preview


@respx.mock
async def test_stackoverflow_api_unavailable_returns_empty() -> None:
    respx.get("https://api.stackexchange.com/2.3/questions/11227809").mock(
        return_value=httpx.Response(503)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/answers").mock(
        return_value=httpx.Response(503)
    )
    respx.get("https://api.stackexchange.com/2.3/questions/11227809/comments").mock(
        return_value=httpx.Response(503)
    )
    updates, ts = await StackOverflowClient().get_updates(11227809, since="1700000000")
    assert updates == []


def _mock_http(response: MagicMock) -> AsyncMock:
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.post.return_value = response
    return mock


async def test_bot_client_sends_update(mocker) -> None:  # type: ignore[no-untyped-def]
    resp = MagicMock()
    resp.status_code = 200
    mocker.patch(
        "scrapper.clients.bot_client.httpx.AsyncClient", return_value=_mock_http(resp)
    )
    await BotClient(base_url="http://bot:8081").send_update(
        LinkUpdate(
            id=1, url="https://github.com/x/y", description="update", tg_chat_ids=[42]
        )
    )


async def test_bot_client_5xx_raises_retryable_error(mocker) -> None:  # type: ignore[no-untyped-def]
    from scrapper.clients.bot_client import BotClientRetryableError

    resp = MagicMock()
    resp.status_code = 500
    mocker.patch(
        "scrapper.clients.bot_client.httpx.AsyncClient", return_value=_mock_http(resp)
    )
    with pytest.raises(BotClientRetryableError):
        await BotClient(base_url="http://bot:8081").send_update(
            LinkUpdate(
                id=1,
                url="https://github.com/x/y",
                description="update",
                tg_chat_ids=[42],
            )
        )


async def test_bot_client_connection_error_raises_retryable_error(mocker) -> None:  # type: ignore[no-untyped-def]
    from scrapper.clients.bot_client import BotClientRetryableError

    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.post.side_effect = httpx.RequestError("connection refused")
    mocker.patch("scrapper.clients.bot_client.httpx.AsyncClient", return_value=mock)
    with pytest.raises(BotClientRetryableError):
        await BotClient(base_url="http://bot:8081").send_update(
            LinkUpdate(
                id=1,
                url="https://github.com/x/y",
                description="update",
                tg_chat_ids=[42],
            )
        )
