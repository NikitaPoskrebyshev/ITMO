from __future__ import annotations

from .config import FilteringConfig
from .models import RawUpdate


class UpdateFilter:
    def __init__(self, config: FilteringConfig) -> None:
        self._config = config

    def should_pass(self, update: RawUpdate) -> bool:
        if len(update.description) < self._config.min_length:
            return False

        lower = update.description.lower()
        for word in self._config.stop_words:
            if word.lower() in lower:
                return False

        if update.author in self._config.excluded_authors:
            return False

        return True
