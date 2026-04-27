from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ChatRepository(Protocol):
    async def register(self, chat_id: int) -> None: ...
    async def exists(self, chat_id: int) -> bool: ...
    async def delete(self, chat_id: int) -> None: ...
    async def all(self, limit: int = 100, offset: int = 0) -> list[int]: ...


@dataclass(slots=True)
class InMemoryUserRepository:
    _started_users: set[int] = field(default_factory=set)

    def is_started(self, user_id: int) -> bool:
        return user_id in self._started_users

    def save_started(self, user_id: int) -> None:
        self._started_users.add(user_id)


@dataclass(slots=True)
class InMemoryChatRepository:
    _chats: set[int] = field(default_factory=set)

    async def register(self, chat_id: int) -> None:
        self._chats.add(chat_id)

    async def exists(self, chat_id: int) -> bool:
        return chat_id in self._chats

    async def delete(self, chat_id: int) -> None:
        self._chats.discard(chat_id)

    async def all(self, limit: int = 100, offset: int = 0) -> list[int]:
        return sorted(self._chats)[offset : offset + limit]


MIGRATIONS_DIR = Path(__file__).parent.parent.parent / "migrations"


async def run_migrations(dsn: str) -> None:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT now()
            )
            """
        )
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for path in migration_files:
            already_applied = await conn.fetchval(
                "SELECT 1 FROM schema_migrations WHERE filename = $1", path.name
            )
            if already_applied:
                continue
            sql = path.read_text(encoding="utf-8")
            await conn.execute(sql)
            await conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES ($1)", path.name
            )
    finally:
        await conn.close()
