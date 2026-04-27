from __future__ import annotations

import logging

import httpx

from ..models.models import LinkUpdate

logger = logging.getLogger(__name__)


class BotClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def send_update(self, update: LinkUpdate) -> None:
        url = f"{self._base_url}/updates"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=update.model_dump(by_alias=True))
            if response.status_code not in (200, 201, 204):
                logger.warning(
                    "bot_client_bad_status_code",
                    extra={"status": response.status_code, "url": url},
                )
        except Exception as exc:
            logger.error("bot_client_failed", extra={"error": str(exc), "url": url})
