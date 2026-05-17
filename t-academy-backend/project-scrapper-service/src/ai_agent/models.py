from __future__ import annotations

from pydantic import BaseModel, Field


class RawUpdate(BaseModel):
    model_config = {"populate_by_name": True}

    id: int
    description: str
    author: str = ""
    tg_chat_ids: list[int] = Field(alias="tgChatIds", default_factory=list)


class ProcessedUpdate(BaseModel):
    id: int
    description: str
    tg_chat_ids: list[int] = Field(serialization_alias="tgChatIds")
    priority: str = "HIGH"
