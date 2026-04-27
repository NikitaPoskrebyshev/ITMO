from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LinkResponse:
    id: int
    url: str
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> LinkResponse:
        return cls(
            id=int(data["id"]),
            url=str(data["url"]),
            tags=[str(t) for t in data.get("tags", [])],
        )


@dataclass
class LinkUpdate:
    id: int
    url: str
    description: str
    tg_chat_ids: list[int]

    @classmethod
    def from_dict(cls, data: dict) -> LinkUpdate:
        required = {"id", "url", "description", "tgChatIds"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        return cls(
            id=int(data["id"]),
            url=str(data["url"]),
            description=str(data["description"]),
            tg_chat_ids=[int(c) for c in data["tgChatIds"]],
        )
