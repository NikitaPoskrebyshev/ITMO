from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel


# --- Domain models (internal) ---

@dataclass(slots=True)
class TrackedLink:
    url: str
    link_type: str  # "github" | "stackoverflow"
    chat_ids: set[int] = field(default_factory=set)
    tags: list[str] = field(default_factory=list)
    last_checked_at: datetime | None = None
    last_known_update: str | None = None


# --- HTTP request/response models ---

class AddLinkRequest(BaseModel):
    link: str
    tags: list[str] = []


class RemoveLinkRequest(BaseModel):
    link: str


class LinkResponse(BaseModel):
    id: int
    url: str
    tags: list[str]


class ListLinksResponse(BaseModel):
    links: list[LinkResponse]
    size: int


class LinkUpdate(BaseModel):
    id: int
    url: str
    description: str
    tg_chat_ids: list[int]


class ApiErrorResponse(BaseModel):
    description: str
    code: str


def link_to_response(link: TrackedLink) -> LinkResponse:
    return LinkResponse(
        id=abs(hash(link.url)),
        url=link.url,
        tags=link.tags,
    )
