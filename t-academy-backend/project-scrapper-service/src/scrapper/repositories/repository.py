from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..models.models import TrackedLink


class ChatNotFoundError(Exception):
    pass


class ChatAlreadyExistsError(Exception):
    pass


class LinkNotFoundError(Exception):
    pass


class LinkAlreadyExistsError(Exception):
    pass


@runtime_checkable
class ScrapperRepository(Protocol):
    async def register_chat(self, chat_id: int) -> None: ...
    async def delete_chat(self, chat_id: int) -> None: ...
    async def get_links_for_chat(self, chat_id: int) -> list[TrackedLink]: ...
    async def add_link(
        self,
        chat_id: int,
        url: str,
        link_type: str,
        tags: list[str],
        filters: list[str] | None = None,
    ) -> TrackedLink: ...
    async def remove_link(self, chat_id: int, url: str) -> TrackedLink: ...
    async def get_all_links(
        self, limit: int = 100, offset: int = 0
    ) -> list[TrackedLink]: ...
    async def update_link_state(self, url: str, last_known_update: str) -> None: ...


_MIGRATIONS_DIR = Path(__file__).parent.parent.parent.parent / "migrations"


async def run_migrations(dsn: str) -> None:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename   TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT now()
            )
            """
        )
        for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
            already = await conn.fetchval(
                "SELECT 1 FROM schema_migrations WHERE filename = $1", path.name
            )
            if already:
                continue
            await conn.execute(path.read_text(encoding="utf-8"))
            await conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES ($1)", path.name
            )
    finally:
        await conn.close()
