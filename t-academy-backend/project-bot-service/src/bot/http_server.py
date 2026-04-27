from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from .models import LinkUpdate

logger = logging.getLogger(__name__)


async def handle_updates_request(
    body: bytes,
    on_update: Callable[[LinkUpdate], Awaitable[None]],
) -> int:
    """Process a POST /updates payload. Returns the HTTP status code."""
    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object")
        update = LinkUpdate.from_dict(data)
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        logger.warning(
            "updates_validation_failed",
            extra={"event": "updates_validation_failed", "error": str(exc)},
        )
        return 400

    try:
        await on_update(update)
        logger.info(
            "updates_received",
            extra={"event": "updates_received", "url": update.url},
        )
        return 200
    except Exception as exc:
        logger.exception(
            "updates_handler_error",
            extra={"event": "updates_handler_error", "error": str(exc)},
        )
        return 400


def _error_response(description: str) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "description": description,
            "code": "BAD_REQUEST",
            "exceptionName": "",
            "exceptionMessage": "",
            "stacktrace": [],
        },
    )


def create_updates_app(
    on_update: Callable[[LinkUpdate], Awaitable[None]],
) -> FastAPI:
    app = FastAPI()

    @app.post("/updates")
    async def updates_endpoint(request: Request) -> Response:
        body = await request.body()
        status = await handle_updates_request(body, on_update)
        if status == 200:
            return Response(status_code=200)
        return _error_response("Некорректные параметры запроса")

    return app
