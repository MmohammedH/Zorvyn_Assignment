import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from log.logger import generate_request_id, get_logger, set_request_id

logger = get_logger(__name__)

_SENSITIVE_HEADERS = frozenset({"authorization", "cookie", "x-api-key", "x-auth-token"})
_EXCLUDED_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = generate_request_id()
        set_request_id(request_id)
        request.state.request_id = request_id

        start_time = time.perf_counter()
        skip = request.url.path in _EXCLUDED_PATHS

        if not skip:
            self._log_request(request)

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "Request failed with unhandled exception",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "elapsed_ms": elapsed,
                    "error": str(exc),
                },
            )
            raise

        elapsed = round((time.perf_counter() - start_time) * 1000, 2)

        if not skip:
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "elapsed_ms": elapsed,
                },
            )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed}ms"
        return response

    def _log_request(self, request: Request) -> None:
        safe_headers = {
            k: ("***" if k.lower() in _SENSITIVE_HEADERS else v)
            for k, v in request.headers.items()
        }
        logger.info(
            "Incoming request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client": request.client.host if request.client else "unknown",
            },
        )
