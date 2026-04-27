from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

import httpx

from .models import LinkResponse

logger = logging.getLogger(__name__)


class ScrapperClientError(Exception):
    pass


class LinkAlreadyTrackedError(ScrapperClientError):
    pass


class LinkNotFoundError(ScrapperClientError):
    pass


class ChatNotFoundError(ScrapperClientError):
    pass


@runtime_checkable
class ScrapperClient(Protocol):
    async def register_chat(self, chat_id: int) -> None: ...
    async def delete_chat(self, chat_id: int) -> None: ...
    async def add_link(
        self, chat_id: int, url: str, tags: list[str], filters: list[str]
    ) -> LinkResponse: ...
    async def remove_link(self, chat_id: int, url: str) -> LinkResponse: ...
    async def list_links(self, chat_id: int) -> list[LinkResponse]: ...


class ScrapperHttpClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def register_chat(self, chat_id: int) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base_url}/tg-chat/{chat_id}")
        if resp.status_code == 409:
            return  # chat already registered — treat as success
        if resp.status_code not in (200, 201, 204):
            raise ScrapperClientError(f"register_chat failed: HTTP {resp.status_code}")
        logger.info(
            "chat_registered",
            extra={"event": "chat_registered", "chat_id": chat_id},
        )

    async def delete_chat(self, chat_id: int) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.delete(f"{self._base_url}/tg-chat/{chat_id}")
        if resp.status_code == 404:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        if resp.status_code not in (200, 204):
            raise ScrapperClientError(f"delete_chat failed: HTTP {resp.status_code}")

    async def add_link(
        self, chat_id: int, url: str, tags: list[str], filters: list[str] | None = None
    ) -> LinkResponse:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/links",
                json={"link": url, "tags": tags, "filters": filters or []},
                headers={"Tg-Chat-Id": str(chat_id)},
            )
        if resp.status_code == 409:
            raise LinkAlreadyTrackedError(f"Link already tracked: {url}")
        if resp.status_code == 404:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        if resp.status_code not in (200, 201):
            raise ScrapperClientError(f"add_link failed: HTTP {resp.status_code}")
        return LinkResponse.from_dict(resp.json())

    async def remove_link(self, chat_id: int, url: str) -> LinkResponse:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.request(
                "DELETE",
                f"{self._base_url}/links",
                json={"link": url},
                headers={"Tg-Chat-Id": str(chat_id)},
            )
        if resp.status_code == 404:
            raise LinkNotFoundError(f"Link {url} not tracked")
        if resp.status_code not in (200, 204):
            raise ScrapperClientError(f"remove_link failed: HTTP {resp.status_code}")
        return LinkResponse.from_dict(resp.json())

    async def list_links(self, chat_id: int) -> list[LinkResponse]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}/links",
                headers={"Tg-Chat-Id": str(chat_id)},
            )
        if resp.status_code == 404:
            raise ChatNotFoundError(f"Chat {chat_id} not found")
        if resp.status_code != 200:
            raise ScrapperClientError(f"list_links failed: HTTP {resp.status_code}")
        return [LinkResponse.from_dict(item) for item in resp.json().get("links", [])]
