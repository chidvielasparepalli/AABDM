"""Global exception handlers → structured error responses.

Shape: {"error": {"code", "message", "request_id", "details?"}}
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")


def _request_id(request: Request) -> str:
    # middleware stashes on request.state before dispatch; header fallback
    rid = getattr(request.state, "request_id", None)
    return rid or request.headers.get("x-request-id", "")


def _err(request: Request, code: str, message: str, status: int, details=None) -> JSONResponse:
    body = {
        "error": {
            "code": code,
            "message": message,
            "request_id": _request_id(request),
        }
    }
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exc(request: Request, exc: StarletteHTTPException):
        logger.warning("http_error", extra={"request_id": _request_id(request), "status": exc.status_code})
        return _err(request, "http_error", str(exc.detail), exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exc(request: Request, exc: RequestValidationError):
        logger.warning("validation_error", extra={"request_id": _request_id(request)})
        details = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []) if p != "body")
            details.append({"field": loc, "message": err.get("msg")})
        return _err(request, "validation_error", "Invalid request payload", 422, details)

    @app.exception_handler(SQLAlchemyError)
    async def db_exc(request: Request, exc: SQLAlchemyError):
        logger.error("db_error", extra={"request_id": _request_id(request)}, exc_info=exc)
        return _err(request, "db_error", "Database error occurred", 500)

    @app.exception_handler(Exception)
    async def unhandled_exc(request: Request, exc: Exception):
        logger.error("unhandled_error", extra={"request_id": _request_id(request)}, exc_info=exc)
        return _err(request, "internal_error", "Internal server error", 500)
