from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LinkResponse:
    id: int
    url: str
    tags: list[str]


@dataclass(frozen=True, slots=True)
class ListLinksResponse:
    links: list[LinkResponse]
    size: int


@dataclass(frozen=True, slots=True)
class AddLinkRequest:
    link: str
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RemoveLinkRequest:
    link: str


@dataclass(frozen=True, slots=True)
class LinkUpdate:
    id: int
    url: str
    description: str
    tg_chat_ids: list[int]
