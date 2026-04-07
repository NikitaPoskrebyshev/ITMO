from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_SO_API = "https://api.stackexchange.com/2.3/questions/{question_id}?site=stackoverflow"


class StackOverflowClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout = timeout_seconds

    async def get_last_update(self, question_id: int) -> str | None:
        url = _SO_API.format(question_id=question_id)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
            if response.status_code != 200:
                logger.warning(
                    "external_api_failed",
                    extra={"event": "stackoverflow_non_2xx", "status": response.status_code, "url": url},
                )
                return None
            items = response.json().get("items", [])
            if not items:
                return None
            return str(items[0].get("last_activity_date", ""))
        except Exception as exc:
            logger.error(
                "external_api_failed",
                extra={"event": "stackoverflow_error", "error": str(exc), "url": url},
            )
            return None
