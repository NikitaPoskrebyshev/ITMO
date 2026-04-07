from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com/repos/{owner}/{repo}"


class GitHubClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout = timeout_seconds

    async def get_last_update(self, owner: str, repo: str) -> str | None:
        url = _GITHUB_API.format(owner=owner, repo=repo)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers={"Accept": "application/vnd.github+json"})
            if response.status_code != 200:
                logger.warning(
                    "external_api_failed",
                    extra={"event": "github_non_2xx", "status": response.status_code, "url": url},
                )
                return None
            return response.json().get("updated_at")
        except Exception as exc:
            logger.error(
                "external_api_failed",
                extra={"event": "github_error", "error": str(exc), "url": url},
            )
            return None
