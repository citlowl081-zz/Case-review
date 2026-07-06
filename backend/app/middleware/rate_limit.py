"""Rate limiting middleware — Redis token bucket."""
import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter (upgrade to Redis for production)."""

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = {}  # key → list of timestamps

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for non-API paths
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Identify user (IP or JWT sub)
        client_key = request.client.host if request.client else "unknown"

        # Clean old timestamps
        now = time.time()
        window = 60  # 1 minute window

        if client_key not in self._requests:
            self._requests[client_key] = []

        self._requests[client_key] = [
            t for t in self._requests[client_key] if now - t < window
        ]

        # Check rate limit
        if len(self._requests[client_key]) >= settings.RATE_LIMIT_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试",
            )

        self._requests[client_key].append(now)
        return await call_next(request)
