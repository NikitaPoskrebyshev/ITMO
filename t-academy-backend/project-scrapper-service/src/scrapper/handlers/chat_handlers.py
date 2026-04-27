from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..repositories.repository import ChatAlreadyExistsError, ChatNotFoundError
from ..services.chat_service import ChatService


def create_chat_router(chat_service: ChatService) -> APIRouter:
    router = APIRouter()

    @router.post("/tg-chat/{id}", status_code=200)
    async def register_chat(id: int) -> dict:
        try:
            await chat_service.register_chat(id)
        except ChatAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {}

    @router.delete("/tg-chat/{id}", status_code=200)
    async def delete_chat(id: int) -> dict:
        try:
            await chat_service.delete_chat(id)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return {}

    return router
