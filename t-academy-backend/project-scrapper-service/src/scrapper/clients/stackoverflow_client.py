from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx

from ..models.models import UpdateInfo

logger = logging.getLogger(__name__)

_BASE = "https://api.stackexchange.com/2.3"
_QUESTION_URL = _BASE + "/questions/{id}?site=stackoverflow"
_ANSWERS_URL = (
    _BASE
    + "/questions/{id}/answers?site=stackoverflow&sort=creation&order=desc&filter=withbody"
)
_COMMENTS_URL = (
    _BASE
    + "/questions/{id}/comments?site=stackoverflow&sort=creation&order=desc&filter=withbody"
)
_PREVIEW_LEN = 200


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _fmt_unix(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


class StackOverflowClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout = timeout_seconds

    async def _get(self, url: str, params: dict | None = None) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.warning(
                    "stackoverflow_non_2xx",
                    extra={"status": response.status_code, "url": url},
                )
                return None
            return response.json()
        except Exception as exc:
            logger.error("stackoverflow_error", extra={"error": str(exc), "url": url})
            return None

    async def get_updates(
        self, question_id: int, since: str | None
    ) -> tuple[list[UpdateInfo], str | None]:
        since_ts = int(since) if since else None

        q_data = await self._get(_QUESTION_URL.format(id=question_id))
        question_title = ""
        if q_data and q_data.get("items"):
            question_title = q_data["items"][0].get("title", "")

        params: dict = {}
        if since_ts:
            params["fromdate"] = since_ts

        answers_data = await self._get(
            _ANSWERS_URL.format(id=question_id), params=params
        )
        comments_data = await self._get(
            _COMMENTS_URL.format(id=question_id), params=params
        )

        answers = (answers_data or {}).get("items", [])
        comments = (comments_data or {}).get("items", [])

        if since is None:
            all_ts = [i.get("creation_date", 0) for i in answers + comments]
            latest = str(max(all_ts)) if all_ts else None
            return [], latest

        updates: list[UpdateInfo] = []
        latest_ts = since_ts or 0

        for answer in answers:
            created = answer.get("creation_date", 0)
            if created <= (since_ts or 0):
                continue
            author = (answer.get("owner") or {}).get("display_name", "unknown")
            body = _strip_html(answer.get("body", "") or "")[:_PREVIEW_LEN]
            latest_ts = max(latest_ts, created)
            updates.append(
                UpdateInfo(
                    update_type="answer",
                    title=f"[Ответ] {question_title}",
                    author=author,
                    created_at=_fmt_unix(created),
                    preview=body,
                    new_timestamp=str(created),
                )
            )

        for comment in comments:
            created = comment.get("creation_date", 0)
            if created <= (since_ts or 0):
                continue
            author = (comment.get("owner") or {}).get("display_name", "unknown")
            body = _strip_html(comment.get("body", "") or "")[:_PREVIEW_LEN]
            latest_ts = max(latest_ts, created)
            updates.append(
                UpdateInfo(
                    update_type="comment",
                    title=f"[Комментарий] {question_title}",
                    author=author,
                    created_at=_fmt_unix(created),
                    preview=body,
                    new_timestamp=str(created),
                )
            )

        new_ts = str(latest_ts) if latest_ts != (since_ts or 0) else since
        return updates, new_ts
