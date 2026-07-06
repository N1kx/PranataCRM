from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.shared.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail
        super().__init__(self.message)


def _module_name(request: Request) -> str:
    path = request.url.path
    prefix = "/api/v1/"
    if path.startswith(prefix):
        rest = path[len(prefix):]
        return rest.split("/", 1)[0] or "unknown"
    return "unknown"


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _log_fields(request: Request) -> dict:
    return {
        "request_id": _request_id(request),
        "user_id": getattr(request.state, "user_id", None),
        "module_name": _module_name(request),
        "endpoint": f"{request.method} {request.url.path}",
    }


def _error_response(
    request: Request, status_code: int, code: str, message: str, detail: str | None
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "detail": detail}},
    )
    request_id = _request_id(request)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        log = logger.warning if exc.status_code < 500 else logger.error
        log(
            "app_exception",
            **_log_fields(request),
            error_details=f"{type(exc).__name__}: {exc.message}"
            + (f" ({exc.detail})" if exc.detail else ""),
        )
        return _error_response(request, exc.status_code, exc.error_code, exc.message, exc.detail)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            **_log_fields(request),
            error_details=f"{type(exc).__name__}: {exc}",
            exc_info=True,
        )
        return _error_response(
            request, 500, "INTERNAL_ERROR", "An unexpected error occurred.", None
        )
