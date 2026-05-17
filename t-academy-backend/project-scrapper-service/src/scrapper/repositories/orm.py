from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    MetaData,
    Table,
    Text,
    TIMESTAMP,
    func,
    select,
    delete,
)
from sqlalchemy.dialects.postgresql import ARRAY, insert
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..models.models import TrackedLink
from .repository import (
    ChatAlreadyExistsError,
    ChatNotFoundError,
    LinkAlreadyExistsError,
    LinkNotFoundError,
    ScrapperRepository,
)

metadata = MetaData()

chats_table = Table(
    "chats",
    metadata,
    Column("chat_id", BigInteger, primary_key=True),
)

links_table = Table(
    "links",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("url", Text, unique=True, nullable=False),
    Column("link_type", Text, nullable=False),
    Column("last_known_update", Text, nullable=True),
    Column("last_checked_at", TIMESTAMP(timezone=True), nullable=True),
)

chat_links_table = Table(
    "chat_links",
    metadata,
    Column(
        "chat_id",
        BigInteger,
        ForeignKey("chats.chat_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "link_id",
        BigInteger,
        ForeignKey("links.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("tags", ARRAY(Text), nullable=False, server_default="{}"),
    Column("filters", ARRAY(Text), nullable=False, server_default="{}"),
)


class OrmScrapperRepository(ScrapperRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def register_chat(self, chat_id: int) -> None:
        async with self._session_factory() as session:
            existing = await session.execute(
                select(chats_table).where(chats_table.c.chat_id == chat_id)
            )
            if existing.first() is not None:
                raise ChatAlreadyExistsError(f"Chat {chat_id} already exists")
            await session.execute(chats_table.insert().values(chat_id=chat_id))
            await session.commit()

    async def delete_chat(self, chat_id: int) -> None:
        async with self._session_factory() as session:
            existing = await session.execute(
                select(chats_table).where(chats_table.c.chat_id == chat_id)
            )
            if existing.first() is None:
                raise ChatNotFoundError(f"Chat {chat_id} not found")
            await session.execute(
                delete(chats_table).where(chats_table.c.chat_id == chat_id)
            )
            subq = select(chat_links_table.c.link_id).distinct()
            await session.execute(
                delete(links_table).where(links_table.c.id.not_in(subq))
            )
            await session.commit()

    async def get_links_for_chat(self, chat_id: int) -> list[TrackedLink]:
        async with self._session_factory() as session:
            existing = await session.execute(
                select(chats_table).where(chats_table.c.chat_id == chat_id)
            )
            if existing.first() is None:
                raise ChatNotFoundError(f"Chat {chat_id} not found")
            result = await session.execute(
                select(
                    links_table.c.url,
                    links_table.c.link_type,
                    links_table.c.last_known_update,
                    links_table.c.last_checked_at,
                    chat_links_table.c.tags,
                    chat_links_table.c.filters,
                )
                .join(chat_links_table, links_table.c.id == chat_links_table.c.link_id)
                .where(chat_links_table.c.chat_id == chat_id)
            )
            return [
                TrackedLink(
                    url=row.url,
                    link_type=row.link_type,
                    chat_ids={chat_id},
                    tags=list(row.tags),
                    filters=list(row.filters),
                    last_known_update=row.last_known_update,
                    last_checked_at=row.last_checked_at,
                )
                for row in result.fetchall()
            ]

    async def add_link(
        self,
        chat_id: int,
        url: str,
        link_type: str,
        tags: list[str],
        filters: list[str] | None = None,
    ) -> TrackedLink:
        filters = filters or []
        async with self._session_factory() as session:
            async with session.begin():
                existing_chat = await session.execute(
                    select(chats_table).where(chats_table.c.chat_id == chat_id)
                )
                if existing_chat.first() is None:
                    raise ChatNotFoundError(f"Chat {chat_id} not found")

                await session.execute(
                    insert(links_table)
                    .values(url=url, link_type=link_type)
                    .on_conflict_do_nothing(index_elements=["url"])
                )
                link_row = await session.execute(
                    select(links_table.c.id).where(links_table.c.url == url)
                )
                link_id = link_row.scalar_one()

                existing_sub = await session.execute(
                    select(chat_links_table).where(
                        chat_links_table.c.chat_id == chat_id,
                        chat_links_table.c.link_id == link_id,
                    )
                )
                if existing_sub.first() is not None:
                    raise LinkAlreadyExistsError(
                        f"Link {url} is already tracked for chat {chat_id}"
                    )

                await session.execute(
                    chat_links_table.insert().values(
                        chat_id=chat_id, link_id=link_id, tags=tags, filters=filters
                    )
                )

                chat_ids_result = await session.execute(
                    select(chat_links_table.c.chat_id).where(
                        chat_links_table.c.link_id == link_id
                    )
                )
                return TrackedLink(
                    url=url,
                    link_type=link_type,
                    chat_ids={r[0] for r in chat_ids_result.fetchall()},
                    tags=list(tags),
                    filters=list(filters),
                )

    async def remove_link(self, chat_id: int, url: str) -> TrackedLink:
        async with self._session_factory() as session:
            async with session.begin():
                existing_chat = await session.execute(
                    select(chats_table).where(chats_table.c.chat_id == chat_id)
                )
                if existing_chat.first() is None:
                    raise ChatNotFoundError(f"Chat {chat_id} not found")

                row_result = await session.execute(
                    select(
                        links_table.c.id,
                        links_table.c.link_type,
                        links_table.c.last_known_update,
                        links_table.c.last_checked_at,
                        chat_links_table.c.tags,
                        chat_links_table.c.filters,
                    )
                    .join(
                        chat_links_table, links_table.c.id == chat_links_table.c.link_id
                    )
                    .where(
                        links_table.c.url == url, chat_links_table.c.chat_id == chat_id
                    )
                )
                row = row_result.first()
                if row is None:
                    raise LinkNotFoundError(f"Link {url} not found for chat {chat_id}")

                link_id = row.id
                await session.execute(
                    delete(chat_links_table).where(
                        chat_links_table.c.chat_id == chat_id,
                        chat_links_table.c.link_id == link_id,
                    )
                )
                remaining = await session.execute(
                    select(chat_links_table.c.chat_id).where(
                        chat_links_table.c.link_id == link_id
                    )
                )
                if remaining.first() is None:
                    await session.execute(
                        delete(links_table).where(links_table.c.id == link_id)
                    )

                return TrackedLink(
                    url=url,
                    link_type=row.link_type,
                    chat_ids=set(),
                    tags=list(row.tags),
                    filters=list(row.filters),
                    last_known_update=row.last_known_update,
                    last_checked_at=row.last_checked_at,
                )

    async def get_all_links(
        self, limit: int = 100, offset: int = 0
    ) -> list[TrackedLink]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(
                    links_table.c.url,
                    links_table.c.link_type,
                    links_table.c.last_known_update,
                    links_table.c.last_checked_at,
                    func.array_agg(chat_links_table.c.chat_id).label("chat_ids"),
                )
                .join(chat_links_table, links_table.c.id == chat_links_table.c.link_id)
                .group_by(
                    links_table.c.id,
                    links_table.c.url,
                    links_table.c.link_type,
                    links_table.c.last_known_update,
                    links_table.c.last_checked_at,
                )
                .order_by(links_table.c.id)
                .limit(limit)
                .offset(offset)
            )
            return [
                TrackedLink(
                    url=row.url,
                    link_type=row.link_type,
                    chat_ids=set(row.chat_ids),
                    last_known_update=row.last_known_update,
                    last_checked_at=row.last_checked_at,
                )
                for row in result.fetchall()
            ]

    async def update_link_state(self, url: str, last_known_update: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                links_table.update()
                .where(links_table.c.url == url)
                .values(last_known_update=last_known_update, last_checked_at=func.now())
            )
            await session.commit()


def create_orm_engine(dsn: str) -> AsyncEngine:
    if dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(dsn, echo=False)


def create_orm_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
