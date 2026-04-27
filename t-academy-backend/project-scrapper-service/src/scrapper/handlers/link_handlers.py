from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Header, HTTPException

from ..models.models import (
    AddLinkRequest,
    LinkResponse,
    ListLinksResponse,
    RemoveLinkRequest,
    link_to_response,
)
from ..repositories.repository import (
    ChatNotFoundError,
    LinkAlreadyExistsError,
    LinkNotFoundError,
)
from ..services.link_parser import InvalidLinkError
from ..services.link_service import LinkService


def create_link_router(link_service: LinkService) -> APIRouter:
    router = APIRouter()

    @router.get("/links", response_model=ListLinksResponse)
    async def get_links(
        tg_chat_id: Annotated[int, Header(alias="Tg-Chat-Id")],
    ) -> ListLinksResponse:
        try:
            links = await link_service.get_links(tg_chat_id)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        items = [link_to_response(link) for link in links]
        return ListLinksResponse(links=items, size=len(items))

    @router.post("/links", response_model=LinkResponse)
    async def add_link(
        request: AddLinkRequest,
        tg_chat_id: Annotated[int, Header(alias="Tg-Chat-Id")],
    ) -> LinkResponse:
        try:
            link = await link_service.add_link(tg_chat_id, request)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except InvalidLinkError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except LinkAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return link_to_response(link)

    @router.delete("/links", response_model=LinkResponse)
    async def remove_link(
        request: Annotated[RemoveLinkRequest, Body()],
        tg_chat_id: Annotated[int, Header(alias="Tg-Chat-Id")],
    ) -> LinkResponse:
        try:
            link = await link_service.remove_link(tg_chat_id, request)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except LinkNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return link_to_response(link)

    return router
