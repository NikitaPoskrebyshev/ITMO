from __future__ import annotations

import asyncio
import logging

from .models import ProcessedUpdate

logger = logging.getLogger(__name__)

_PRIORITY_ORDER: dict[str, int] = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}


def _max_priority(priorities: list[str]) -> str:
    return max(priorities, key=lambda p: _PRIORITY_ORDER.get(p, 0))


class MessageGrouper:
    def __init__(self, window_ms: int) -> None:
        self._window_ms = window_ms
        self._buffers: dict[int, list[ProcessedUpdate]] = {}
        self._output: asyncio.Queue[ProcessedUpdate] = asyncio.Queue()

    async def add(self, update: ProcessedUpdate) -> None:
        loop = asyncio.get_running_loop()
        for chat_id in update.tg_chat_ids:
            if chat_id not in self._buffers:
                self._buffers[chat_id] = []
                loop.call_later(
                    self._window_ms / 1000,
                    lambda cid=chat_id: asyncio.ensure_future(self._flush(cid)),
                )
            self._buffers[chat_id].append(update)

    async def _flush(self, chat_id: int) -> None:
        updates = self._buffers.pop(chat_id, [])
        if updates:
            await self._output.put(self._build_message(updates, chat_id))

    @staticmethod
    def _build_message(updates: list[ProcessedUpdate], chat_id: int) -> ProcessedUpdate:
        if len(updates) == 1:
            return updates[0]
        description = "\n".join(
            f"{i + 1}. {u.description}" for i, u in enumerate(updates)
        )
        return ProcessedUpdate(
            id=updates[0].id,
            description=description,
            tg_chat_ids=[chat_id],
            priority=_max_priority([u.priority for u in updates]),
        )

    @property
    def output(self) -> asyncio.Queue[ProcessedUpdate]:
        return self._output
