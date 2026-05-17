from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field


@dataclass(slots=True)
class UpdateInfo:
    update_type: str
    title: str
    author: str
    created_at: str
    preview: str
    new_timestamp: str


@dataclass(slots=True)
class TrackedLink:
    url: str
    link_type: str  # "github" | "stackoverflow"
    chat_ids: set[int] = field(default_factory=set)
    tags: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    last_checked_at: datetime | None = None
    last_known_update: str | None = None


class AddLinkRequest(BaseModel):
    link: str
    tags: list[str] = []
    filters: list[str] = []


class RemoveLinkRequest(BaseModel):
    link: str


class LinkResponse(BaseModel):
    id: int
    url: str
    tags: list[str]
    filters: list[str]


class ListLinksResponse(BaseModel):
    links: list[LinkResponse]
    size: int


class LinkUpdate(BaseModel):
    id: int
    url: str
    description: str
    author: str = ""
    tg_chat_ids: list[int] = Field(serialization_alias="tgChatIds")


class ApiErrorResponse(BaseModel):
    description: str | None = None
    code: str | None = None
    exception_name: str | None = Field(None, alias="exceptionName")
    exception_message: str | None = Field(None, alias="exceptionMessage")
    stacktrace: list[str] = []


def link_to_response(link: TrackedLink) -> LinkResponse:
    return LinkResponse(
        id=abs(hash(link.url)),
        url=link.url,
        tags=link.tags,
        filters=link.filters,
    )
