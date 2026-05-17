from __future__ import annotations

import logging

import httpx

from ..models.models import LinkUpdate

logger = logging.getLogger(__name__)


class BotClientError(Exception):
    pass


class BotClientRetryableError(BotClientError):
    """5xx or timeout"""


class BotClientNonRetryableError(BotClientError):
    """4xx"""


class BotClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 10,
        retryable_status_codes: tuple[int, ...] = (500, 502, 503, 504),
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._retryable = set(retryable_status_codes)

    async def send_update(self, update: LinkUpdate) -> None:
        url = f"{self._base_url}/updates"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=update.model_dump(by_alias=True))
        except httpx.TimeoutException as exc:
            raise BotClientRetryableError(f"timeout: {exc}") from exc
        except httpx.RequestError as exc:
            raise BotClientRetryableError(f"connection error: {exc}") from exc

        if response.status_code in (200, 201, 204):
            return

        if response.status_code in self._retryable:
            raise BotClientRetryableError(f"HTTP {response.status_code}")

        raise BotClientNonRetryableError(f"HTTP {response.status_code}")
