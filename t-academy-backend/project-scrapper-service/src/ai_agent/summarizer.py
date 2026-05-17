from __future__ import annotations

from .config import SummarizationConfig


class TruncatingSummarizer:
    def __init__(self, config: SummarizationConfig) -> None:
        self._threshold = config.threshold

    async def summarize(self, text: str) -> str:
        if len(text) <= self._threshold:
            return text
        return text[: self._threshold] + "..."
