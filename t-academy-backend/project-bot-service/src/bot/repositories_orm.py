from __future__ import annotations

from sqlalchemy import BigInteger, Column, Table, MetaData, select, delete
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.dialects.postgresql import insert

metadata = MetaData()

chats_table = Table(
    "chats",
    metadata,
    Column("chat_id", BigInteger, primary_key=True),
)


class OrmChatRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def register(self, chat_id: int) -> None:
        async with self._session_factory() as session:
            stmt = insert(chats_table).values(chat_id=chat_id).on_conflict_do_nothing()
            await session.execute(stmt)
            await session.commit()

    async def exists(self, chat_id: int) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                select(chats_table).where(chats_table.c.chat_id == chat_id)
            )
            return result.first() is not None

    async def delete(self, chat_id: int) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(chats_table).where(chats_table.c.chat_id == chat_id)
            )
            await session.commit()

    async def all(self, limit: int = 100, offset: int = 0) -> list[int]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(chats_table.c.chat_id)
                .order_by(chats_table.c.chat_id)
                .limit(limit)
                .offset(offset)
            )
            return [row[0] for row in result.fetchall()]


def create_orm_engine(dsn: str) -> AsyncEngine:
    # asyncpg driver requires postgresql+asyncpg scheme
    if dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(dsn, echo=False)


def create_orm_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
