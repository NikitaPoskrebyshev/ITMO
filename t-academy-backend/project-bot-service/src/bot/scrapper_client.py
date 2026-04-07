from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Protocol

from bot.models import AddLinkRequest, LinkResponse, ListLinksResponse, RemoveLinkRequest

logger = logging.getLogger(__name__)


class ScrapperError(Exception):
    """Raised when the scrapper-service returns an error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class DuplicateLinkError(ScrapperError):
    """Raised when the link is already tracked for this chat."""


class InvalidLinkError(ScrapperError):
    """Raised when the link format is not supported by scrapper."""


class LinkNotFoundError(ScrapperError):
    """Raised when the link is not found in the chat's tracked links."""


class ChatNotFoundError(ScrapperError):
    """Raised when the chat is not registered in the scrapper."""


class ScrapperClient(Protocol):
    async def register_chat(self, chat_id: int) -> None: ...

    async def add_link(self, chat_id: int, request: AddLinkRequest) -> LinkResponse: ...

    async def remove_link(
        self, chat_id: int, request: RemoveLinkRequest
    ) -> LinkResponse: ...

    async def list_links(self, chat_id: int) -> ListLinksResponse: ...


class ScrapperHttpClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def _do_request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str | int] | None = None,
        body: dict | None = None,
    ) -> dict:
        url = f"{self._base_url}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, str(v))
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                content = resp.read().decode()
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode() if exc.fp else ""
            self._raise_scrapper_error(exc.code, error_body)
            raise  # unreachable, satisfies type checker

    @staticmethod
    def _raise_scrapper_error(status_code: int, body: str) -> None:
        try:
            detail = json.loads(body).get("detail", body)
        except (json.JSONDecodeError, AttributeError):
            detail = body

        if status_code == 404:
            if "chat" in detail.lower():
                raise ChatNotFoundError(status_code, detail)
            raise LinkNotFoundError(status_code, detail)

        if status_code == 400:
            if "already" in detail.lower():
                raise DuplicateLinkError(status_code, detail)
            raise InvalidLinkError(status_code, detail)

        raise ScrapperError(status_code, detail)

    async def register_chat(self, chat_id: int) -> None:
        await asyncio.to_thread(self._do_request, "POST", f"/tg-chat/{chat_id}")

    async def add_link(self, chat_id: int, request: AddLinkRequest) -> LinkResponse:
        data = await asyncio.to_thread(
            self._do_request,
            "POST",
            "/links",
            headers={"Tg-Chat-Id": chat_id},
            body={"link": request.link, "tags": list(request.tags)},
        )
        return LinkResponse(id=data["id"], url=data["url"], tags=data["tags"])

    async def remove_link(
        self, chat_id: int, request: RemoveLinkRequest
    ) -> LinkResponse:
        data = await asyncio.to_thread(
            self._do_request,
            "DELETE",
            "/links",
            headers={"Tg-Chat-Id": chat_id},
            body={"link": request.link},
        )
        return LinkResponse(id=data["id"], url=data["url"], tags=data["tags"])

    async def list_links(self, chat_id: int) -> ListLinksResponse:
        data = await asyncio.to_thread(
            self._do_request,
            "GET",
            "/links",
            headers={"Tg-Chat-Id": chat_id},
        )
        links = [
            LinkResponse(id=item["id"], url=item["url"], tags=item["tags"])
            for item in data["links"]
        ]
        return ListLinksResponse(links=links, size=data["size"])
