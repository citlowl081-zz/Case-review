"""Request logging middleware."""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        # Log request
        logger.info(f"[{request_id}] → {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            duration = (time.time() - start) * 1000
            logger.info(
                f"[{request_id}] ← {response.status_code} ({duration:.0f}ms)"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error(f"[{request_id}] ✗ {type(e).__name__} ({duration:.0f}ms)")
            raise

        return response
