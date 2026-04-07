from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


@dataclass(slots=True)
class InMemoryUserRepository:
    _started_users: set[int] = field(default_factory=set)

    def is_started(self, user_id: int) -> bool:
        return user_id in self._started_users

    def save_started(self, user_id: int) -> None:
        self._started_users.add(user_id)


class TrackDialogState(Enum):
    IDLE = auto()
    WAITING_FOR_TRACK_URL = auto()
    WAITING_FOR_TRACK_TAGS = auto()
    WAITING_FOR_UNTRACK_URL = auto()


@dataclass(slots=True)
class TrackSession:
    state: TrackDialogState = TrackDialogState.IDLE
    pending_url: str | None = None


@dataclass(slots=True)
class InMemoryTrackStateRepository:
    _sessions: dict[int, TrackSession] = field(default_factory=dict)

    def get_session(self, chat_id: int) -> TrackSession:
        return self._sessions.get(chat_id, TrackSession())

    def set_session(self, chat_id: int, session: TrackSession) -> None:
        self._sessions[chat_id] = session

    def clear_session(self, chat_id: int) -> None:
        self._sessions.pop(chat_id, None)
