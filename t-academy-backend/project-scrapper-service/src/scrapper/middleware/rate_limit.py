from __future__ import annotations

from limits import parse, storage, strategies
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 100) -> None:
        super().__init__(app)
        mem = storage.MemoryStorage()
        self._strategy = strategies.FixedWindowRateLimiter(mem)
        self._limit = parse(f"{requests_per_minute}/minute")

    async def dispatch(self, request: Request, call_next) -> Response:
        key = request.client.host if request.client else "127.0.0.1"
        if not self._strategy.hit(self._limit, "rate", key):
            return JSONResponse(
                status_code=429,
                content={"description": "Too many requests", "code": "429"},
            )
        return await call_next(request)
