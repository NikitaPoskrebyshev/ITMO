from __future__ import annotations


import asyncpg

from ..models.models import TrackedLink
from .repository import (
    ChatAlreadyExistsError,
    ChatNotFoundError,
    LinkAlreadyExistsError,
    LinkNotFoundError,
    ScrapperRepository,
)


class SqlScrapperRepository(ScrapperRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def register_chat(self, chat_id: int) -> None:
        async with self._pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT 1 FROM chats WHERE chat_id = $1", chat_id
            )
            if existing:
                raise ChatAlreadyExistsError(f"Chat {chat_id} already exists")
            await conn.execute("INSERT INTO chats (chat_id) VALUES ($1)", chat_id)

    async def delete_chat(self, chat_id: int) -> None:
        async with self._pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT 1 FROM chats WHERE chat_id = $1", chat_id
            )
            if not existing:
                raise ChatNotFoundError(f"Chat {chat_id} not found")
            await conn.execute("DELETE FROM chats WHERE chat_id = $1", chat_id)
            await conn.execute(
                "DELETE FROM links WHERE id NOT IN (SELECT DISTINCT link_id FROM chat_links)"
            )

    async def get_links_for_chat(self, chat_id: int) -> list[TrackedLink]:
        async with self._pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT 1 FROM chats WHERE chat_id = $1", chat_id
            )
            if not existing:
                raise ChatNotFoundError(f"Chat {chat_id} not found")
            rows = await conn.fetch(
                """
                SELECT l.url, l.link_type, l.last_known_update, l.last_checked_at,
                       cl.tags, cl.filters
                FROM links l
                JOIN chat_links cl ON l.id = cl.link_id
                WHERE cl.chat_id = $1
                """,
                chat_id,
            )
            return [_row_to_link(row, {chat_id}) for row in rows]

    async def add_link(
        self,
        chat_id: int,
        url: str,
        link_type: str,
        tags: list[str],
        filters: list[str] | None = None,
    ) -> TrackedLink:
        filters = filters or []
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                existing_chat = await conn.fetchrow(
                    "SELECT 1 FROM chats WHERE chat_id = $1", chat_id
                )
                if not existing_chat:
                    raise ChatNotFoundError(f"Chat {chat_id} not found")

                await conn.execute(
                    "INSERT INTO links (url, link_type) VALUES ($1, $2) ON CONFLICT (url) DO NOTHING",
                    url,
                    link_type,
                )
                link_row = await conn.fetchrow(
                    "SELECT id FROM links WHERE url = $1", url
                )
                link_id = link_row["id"]

                existing_sub = await conn.fetchrow(
                    "SELECT 1 FROM chat_links WHERE chat_id = $1 AND link_id = $2",
                    chat_id,
                    link_id,
                )
                if existing_sub:
                    raise LinkAlreadyExistsError(
                        f"Link {url} is already tracked for chat {chat_id}"
                    )

                await conn.execute(
                    "INSERT INTO chat_links (chat_id, link_id, tags, filters) VALUES ($1, $2, $3, $4)",
                    chat_id,
                    link_id,
                    tags,
                    filters,
                )

                chat_ids = await conn.fetch(
                    "SELECT chat_id FROM chat_links WHERE link_id = $1", link_id
                )
                return TrackedLink(
                    url=url,
                    link_type=link_type,
                    chat_ids={r["chat_id"] for r in chat_ids},
                    tags=list(tags),
                    filters=list(filters),
                )

    async def remove_link(self, chat_id: int, url: str) -> TrackedLink:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                existing_chat = await conn.fetchrow(
                    "SELECT 1 FROM chats WHERE chat_id = $1", chat_id
                )
                if not existing_chat:
                    raise ChatNotFoundError(f"Chat {chat_id} not found")

                row = await conn.fetchrow(
                    """
                    SELECT l.id, l.link_type, l.last_known_update, l.last_checked_at,
                           cl.tags, cl.filters
                    FROM links l
                    JOIN chat_links cl ON l.id = cl.link_id
                    WHERE l.url = $1 AND cl.chat_id = $2
                    """,
                    url,
                    chat_id,
                )
                if not row:
                    raise LinkNotFoundError(f"Link {url} not found for chat {chat_id}")

                link_id = row["id"]
                await conn.execute(
                    "DELETE FROM chat_links WHERE chat_id = $1 AND link_id = $2",
                    chat_id,
                    link_id,
                )
                remaining = await conn.fetchrow(
                    "SELECT 1 FROM chat_links WHERE link_id = $1", link_id
                )
                if not remaining:
                    await conn.execute("DELETE FROM links WHERE id = $1", link_id)

                return TrackedLink(
                    url=url,
                    link_type=row["link_type"],
                    chat_ids=set(),
                    tags=list(row["tags"]),
                    filters=list(row["filters"]),
                    last_known_update=row["last_known_update"],
                    last_checked_at=row["last_checked_at"],
                )

    async def get_all_links(self, limit: int = 100, offset: int = 0) -> list[TrackedLink]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT l.url, l.link_type, l.last_known_update, l.last_checked_at,
                       array_agg(cl.chat_id) AS chat_ids
                FROM links l
                JOIN chat_links cl ON l.id = cl.link_id
                GROUP BY l.id, l.url, l.link_type, l.last_known_update, l.last_checked_at
                ORDER BY l.id
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            return [
                TrackedLink(
                    url=row["url"],
                    link_type=row["link_type"],
                    chat_ids=set(row["chat_ids"]),
                    last_known_update=row["last_known_update"],
                    last_checked_at=row["last_checked_at"],
                )
                for row in rows
            ]

    async def update_link_state(self, url: str, last_known_update: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE links SET last_known_update = $1, last_checked_at = now() WHERE url = $2",
                last_known_update,
                url,
            )


def _row_to_link(row: asyncpg.Record, chat_ids: set[int]) -> TrackedLink:
    return TrackedLink(
        url=row["url"],
        link_type=row["link_type"],
        chat_ids=chat_ids,
        tags=list(row["tags"]),
        filters=list(row["filters"]),
        last_known_update=row["last_known_update"],
        last_checked_at=row["last_checked_at"],
    )


async def create_sql_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn)
