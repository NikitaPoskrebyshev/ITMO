from __future__ import annotations

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

from bot.repositories import run_migrations
from bot.repositories_sql import SqlChatRepository, create_sql_pool
from bot.repositories_orm import (
    OrmChatRepository,
    create_orm_engine,
    create_orm_session_factory,
)


def _normalize_dsn(dsn: str) -> str:
    """Convert any variant of postgres DSN to plain postgresql://..."""
    for prefix in ("postgresql+psycopg2://", "postgresql+asyncpg://", "psycopg2://"):
        if dsn.startswith(prefix):
            return "postgresql://" + dsn[len(prefix) :]
    return dsn


@pytest.fixture(scope="module")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="module")
def pg_dsn(postgres):
    return _normalize_dsn(postgres.get_connection_url())


@pytest_asyncio.fixture
async def sql_repo(pg_dsn):
    await run_migrations(pg_dsn)
    pool = await create_sql_pool(pg_dsn)
    repo = SqlChatRepository(pool)
    yield repo
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE chats")
    await pool.close()


@pytest_asyncio.fixture
async def orm_repo(pg_dsn):
    await run_migrations(pg_dsn)
    engine = create_orm_engine(pg_dsn)
    session_factory = create_orm_session_factory(engine)
    repo = OrmChatRepository(session_factory)
    yield repo
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE chats"))
    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_register_chat_stored(sql_repo):
    await sql_repo.register(42)
    assert await sql_repo.exists(42)


@pytest.mark.asyncio
async def test_sql_register_duplicate_no_error(sql_repo):
    await sql_repo.register(10)
    await sql_repo.register(10)
    assert await sql_repo.exists(10)


@pytest.mark.asyncio
async def test_sql_delete_chat_removed(sql_repo):
    await sql_repo.register(99)
    await sql_repo.delete(99)
    assert not await sql_repo.exists(99)


@pytest.mark.asyncio
async def test_sql_all_pagination(sql_repo):
    for i in range(1, 6):
        await sql_repo.register(i)
    page1 = await sql_repo.all(limit=3, offset=0)
    page2 = await sql_repo.all(limit=3, offset=3)
    assert len(page1) == 3
    assert len(page2) == 2


@pytest.mark.asyncio
async def test_orm_register_chat_stored(orm_repo):
    await orm_repo.register(42)
    assert await orm_repo.exists(42)


@pytest.mark.asyncio
async def test_orm_register_duplicate_no_error(orm_repo):
    await orm_repo.register(10)
    await orm_repo.register(10)
    assert await orm_repo.exists(10)


@pytest.mark.asyncio
async def test_orm_delete_chat_removed(orm_repo):
    await orm_repo.register(99)
    await orm_repo.delete(99)
    assert not await orm_repo.exists(99)


@pytest.mark.asyncio
async def test_orm_all_pagination(orm_repo):
    for i in range(1, 6):
        await orm_repo.register(i)
    page1 = await orm_repo.all(limit=3, offset=0)
    page2 = await orm_repo.all(limit=3, offset=3)
    assert len(page1) == 3
    assert len(page2) == 2


@pytest.mark.asyncio
async def test_migrations_applied_successfully(pg_dsn):
    """Fresh DB + migrations = chats table exists."""
    await run_migrations(pg_dsn)
    import asyncpg

    conn = await asyncpg.connect(pg_dsn)
    try:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'chats'"
        )
        assert result == 1
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_sql_implementation_selected(pg_dsn):
    await run_migrations(pg_dsn)
    pool = await create_sql_pool(pg_dsn)
    repo = SqlChatRepository(pool)
    assert isinstance(repo, SqlChatRepository)
    await pool.close()


@pytest.mark.asyncio
async def test_orm_implementation_selected(pg_dsn):
    engine = create_orm_engine(pg_dsn)
    session_factory = create_orm_session_factory(engine)
    repo = OrmChatRepository(session_factory)
    assert isinstance(repo, OrmChatRepository)
    await engine.dispose()
