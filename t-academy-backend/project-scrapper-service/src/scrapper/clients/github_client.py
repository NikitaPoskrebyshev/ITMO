from __future__ import annotations

import logging

import httpx

from ..models.models import UpdateInfo

logger = logging.getLogger(__name__)

_ISSUES_URL = "https://api.github.com/repos/{owner}/{repo}/issues"
_HEADERS = {"Accept": "application/vnd.github+json"}
_PREVIEW_LEN = 200


def _fmt_iso(iso: str) -> str:
    return iso.replace("T", " ").replace("Z", " UTC")


class GitHubClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout = timeout_seconds

    async def get_updates(
        self, owner: str, repo: str, since: str | None
    ) -> tuple[list[UpdateInfo], str | None]:
        url = _ISSUES_URL.format(owner=owner, repo=repo)
        params = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": 30,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=_HEADERS, params=params)
            if response.status_code != 200:
                logger.warning(
                    "github_non_2xx",
                    extra={"status": response.status_code, "url": url},
                )
                return [], None
            items = response.json()
            if not items:
                return [], None

            latest_timestamp: str = items[0].get("created_at", "")

            if since is None:
                return [], latest_timestamp

            updates: list[UpdateInfo] = []
            for item in items:
                created_at: str = item.get("created_at", "")
                if created_at <= since:
                    break
                is_pr = "pull_request" in item
                kind = "PR" if is_pr else "Issue"
                number = item.get("number", 0)
                title = f"[{kind} #{number}] {item.get('title', '')}"
                author = (item.get("user") or {}).get("login", "unknown")
                body = (item.get("body") or "")[:_PREVIEW_LEN]
                updates.append(
                    UpdateInfo(
                        update_type="pull_request" if is_pr else "issue",
                        title=title,
                        author=author,
                        created_at=_fmt_iso(created_at),
                        preview=body,
                        new_timestamp=created_at,
                    )
                )

            new_ts = updates[0].new_timestamp if updates else since
            return updates, new_ts

        except Exception as exc:
            logger.error("github_error", extra={"error": str(exc), "url": url})
            return [], None
