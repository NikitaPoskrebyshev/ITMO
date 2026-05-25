from __future__ import annotations

from .config import PrioritizationConfig


class Prioritizer:
    def __init__(self, config: PrioritizationConfig) -> None:
        self._high = config.high_keywords
        self._low = config.low_keywords

    def assign(self, text: str) -> str:
        lower = text.lower()
        if any(kw.lower() in lower for kw in self._high):
            return "HIGH"
        if any(kw.lower() in lower for kw in self._low):
            return "LOW"
        return "MEDIUM"
