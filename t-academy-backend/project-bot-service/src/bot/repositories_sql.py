from __future__ import annotations

import asyncpg


class SqlChatRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def register(self, chat_id: int) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO chats (chat_id) VALUES ($1) ON CONFLICT DO NOTHING",
                chat_id,
            )

    async def exists(self, chat_id: int) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT 1 FROM chats WHERE chat_id = $1", chat_id)
            return row is not None

    async def delete(self, chat_id: int) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM chats WHERE chat_id = $1", chat_id)

    async def all(self, limit: int = 100, offset: int = 0) -> list[int]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT chat_id FROM chats ORDER BY chat_id LIMIT $1 OFFSET $2",
                limit,
                offset,
            )
            return [row["chat_id"] for row in rows]


async def create_sql_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn)
