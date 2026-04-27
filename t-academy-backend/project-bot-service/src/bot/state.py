from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TrackState(Enum):
    IDLE = "idle"
    WAITING_FOR_TRACK_URL = "waiting_for_track_url"
    WAITING_FOR_TRACK_TAGS = "waiting_for_track_tags"
    WAITING_FOR_TRACK_FILTERS = "waiting_for_track_filters"
    WAITING_FOR_UNTRACK_URL = "waiting_for_untrack_url"


@dataclass
class TrackSession:
    state: TrackState = TrackState.IDLE
    pending_url: str | None = None
    pending_tags: list[str] = field(default_factory=list)


class InMemoryStateRepository:
    def __init__(self) -> None:
        self._sessions: dict[int, TrackSession] = {}

    def get(self, chat_id: int) -> TrackSession:
        return self._sessions.setdefault(chat_id, TrackSession())

    def reset(self, chat_id: int) -> None:
        self._sessions[chat_id] = TrackSession()

    def set_state(
        self,
        chat_id: int,
        state: TrackState,
        pending_url: str | None = None,
        pending_tags: list[str] | None = None,
    ) -> None:
        session = self.get(chat_id)
        session.state = state
        session.pending_url = pending_url
        session.pending_tags = pending_tags if pending_tags is not None else []
