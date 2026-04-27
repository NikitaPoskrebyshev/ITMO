from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

from scrapper.repositories.orm import (
    OrmScrapperRepository,
    create_orm_engine,
    create_orm_session_factory,
)
from scrapper.repositories.repository import (
    ChatAlreadyExistsError,
    ChatNotFoundError,
    LinkAlreadyExistsError,
    LinkNotFoundError,
    run_migrations,
)
from scrapper.repositories.sql import SqlScrapperRepository, create_sql_pool

GITHUB_URL = "https://github.com/octocat/Hello-World"


def _normalize_dsn(url: str) -> str:
    for prefix in ("postgresql+psycopg2://", "postgresql+psycopg://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix) :]
    return url


@pytest.fixture(scope="module")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="module")
def pg_dsn(postgres: PostgresContainer) -> str:
    return _normalize_dsn(postgres.get_connection_url())


@pytest_asyncio.fixture
async def sql_repo(pg_dsn: str) -> SqlScrapperRepository:
    await run_migrations(pg_dsn)
    pool = await create_sql_pool(pg_dsn)
    repo = SqlScrapperRepository(pool)
    yield repo  # type: ignore[misc]
    async with pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE chat_links, links, chats, schema_migrations RESTART IDENTITY CASCADE"
        )
    await pool.close()


@pytest_asyncio.fixture
async def orm_repo(pg_dsn: str) -> OrmScrapperRepository:
    await run_migrations(pg_dsn)
    engine = create_orm_engine(pg_dsn)
    session_factory = create_orm_session_factory(engine)
    repo = OrmScrapperRepository(session_factory)
    yield repo  # type: ignore[misc]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE chat_links, links, chats, schema_migrations RESTART IDENTITY CASCADE"
            )
        )
    await engine.dispose()


async def _setup(
    repo: SqlScrapperRepository | OrmScrapperRepository, chat_id: int = 1
) -> None:
    await repo.register_chat(chat_id)


# ============================================================
# SQL tests
# ============================================================


async def test_sql_register_chat(sql_repo: SqlScrapperRepository) -> None:
    await sql_repo.register_chat(1)


async def test_sql_register_duplicate_chat_raises(
    sql_repo: SqlScrapperRepository,
) -> None:
    await sql_repo.register_chat(1)
    with pytest.raises(ChatAlreadyExistsError):
        await sql_repo.register_chat(1)


async def test_sql_delete_chat(sql_repo: SqlScrapperRepository) -> None:
    await sql_repo.register_chat(1)
    await sql_repo.delete_chat(1)


async def test_sql_delete_nonexistent_chat_raises(
    sql_repo: SqlScrapperRepository,
) -> None:
    with pytest.raises(ChatNotFoundError):
        await sql_repo.delete_chat(999)


async def test_sql_add_link_stored_in_db(sql_repo: SqlScrapperRepository) -> None:
    await _setup(sql_repo)
    link = await sql_repo.add_link(1, GITHUB_URL, "github", ["tag1"], ["filter1"])
    assert link.url == GITHUB_URL
    assert "tag1" in link.tags
    assert "filter1" in link.filters


async def test_sql_add_duplicate_link_raises(sql_repo: SqlScrapperRepository) -> None:
    await _setup(sql_repo)
    await sql_repo.add_link(1, GITHUB_URL, "github", [])
    with pytest.raises(LinkAlreadyExistsError):
        await sql_repo.add_link(1, GITHUB_URL, "github", [])


async def test_sql_remove_link(sql_repo: SqlScrapperRepository) -> None:
    await _setup(sql_repo)
    await sql_repo.add_link(1, GITHUB_URL, "github", [])
    removed = await sql_repo.remove_link(1, GITHUB_URL)
    assert removed.url == GITHUB_URL
    links = await sql_repo.get_links_for_chat(1)
    assert links == []


async def test_sql_remove_nonexistent_link_raises(
    sql_repo: SqlScrapperRepository,
) -> None:
    await _setup(sql_repo)
    with pytest.raises(LinkNotFoundError):
        await sql_repo.remove_link(1, GITHUB_URL)


async def test_sql_get_all_links_with_chat_ids(sql_repo: SqlScrapperRepository) -> None:
    await sql_repo.register_chat(1)
    await sql_repo.register_chat(2)
    await sql_repo.add_link(1, GITHUB_URL, "github", [])
    await sql_repo.add_link(2, GITHUB_URL, "github", [])
    all_links = await sql_repo.get_all_links()
    assert len(all_links) == 1
    assert {1, 2} == all_links[0].chat_ids


async def test_sql_update_link_state(sql_repo: SqlScrapperRepository) -> None:
    await _setup(sql_repo)
    await sql_repo.add_link(1, GITHUB_URL, "github", [])
    await sql_repo.update_link_state(GITHUB_URL, "2024-01-01T00:00:00Z")
    all_links = await sql_repo.get_all_links()
    assert all_links[0].last_known_update == "2024-01-01T00:00:00Z"


async def test_sql_migrations_applied_on_fresh_db(
    sql_repo: SqlScrapperRepository,
) -> None:
    await sql_repo.register_chat(42)


# ============================================================
# ORM tests (same scenarios)
# ============================================================


async def test_orm_register_chat(orm_repo: OrmScrapperRepository) -> None:
    await orm_repo.register_chat(1)


async def test_orm_register_duplicate_chat_raises(
    orm_repo: OrmScrapperRepository,
) -> None:
    await orm_repo.register_chat(1)
    with pytest.raises(ChatAlreadyExistsError):
        await orm_repo.register_chat(1)


async def test_orm_delete_chat(orm_repo: OrmScrapperRepository) -> None:
    await orm_repo.register_chat(1)
    await orm_repo.delete_chat(1)


async def test_orm_delete_nonexistent_chat_raises(
    orm_repo: OrmScrapperRepository,
) -> None:
    with pytest.raises(ChatNotFoundError):
        await orm_repo.delete_chat(999)


async def test_orm_add_link_stored_in_db(orm_repo: OrmScrapperRepository) -> None:
    await _setup(orm_repo)
    link = await orm_repo.add_link(1, GITHUB_URL, "github", ["tag1"], ["filter1"])
    assert link.url == GITHUB_URL
    assert "tag1" in link.tags
    assert "filter1" in link.filters


async def test_orm_add_duplicate_link_raises(orm_repo: OrmScrapperRepository) -> None:
    await _setup(orm_repo)
    await orm_repo.add_link(1, GITHUB_URL, "github", [])
    with pytest.raises(LinkAlreadyExistsError):
        await orm_repo.add_link(1, GITHUB_URL, "github", [])


async def test_orm_remove_link(orm_repo: OrmScrapperRepository) -> None:
    await _setup(orm_repo)
    await orm_repo.add_link(1, GITHUB_URL, "github", [])
    removed = await orm_repo.remove_link(1, GITHUB_URL)
    assert removed.url == GITHUB_URL
    links = await orm_repo.get_links_for_chat(1)
    assert links == []


async def test_orm_remove_nonexistent_link_raises(
    orm_repo: OrmScrapperRepository,
) -> None:
    await _setup(orm_repo)
    with pytest.raises(LinkNotFoundError):
        await orm_repo.remove_link(1, GITHUB_URL)


async def test_orm_get_all_links_with_chat_ids(orm_repo: OrmScrapperRepository) -> None:
    await orm_repo.register_chat(1)
    await orm_repo.register_chat(2)
    await orm_repo.add_link(1, GITHUB_URL, "github", [])
    await orm_repo.add_link(2, GITHUB_URL, "github", [])
    all_links = await orm_repo.get_all_links()
    assert len(all_links) == 1
    assert {1, 2} == all_links[0].chat_ids


async def test_orm_update_link_state(orm_repo: OrmScrapperRepository) -> None:
    await _setup(orm_repo)
    await orm_repo.add_link(1, GITHUB_URL, "github", [])
    await orm_repo.update_link_state(GITHUB_URL, "2024-01-01T00:00:00Z")
    all_links = await orm_repo.get_all_links()
    assert all_links[0].last_known_update == "2024-01-01T00:00:00Z"


async def test_orm_migrations_applied_on_fresh_db(
    orm_repo: OrmScrapperRepository,
) -> None:
    await orm_repo.register_chat(42)
