"""
Custom HTTP exceptions and FastAPI exception handlers.

Provides thin wrappers around ``HTTPException`` so that raising a domain
error is one-liner, and exception handlers return consistent JSON shapes.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------

class NotFoundException(HTTPException):
    """404 — Resource not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(HTTPException):
    """400 — Client sent an invalid request."""

    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(HTTPException):
    """401 — Authentication required or failed."""

    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    """403 — Authenticated but lacking permissions."""

    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictException(HTTPException):
    """409 — Conflict with existing resource state."""

    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


# ---------------------------------------------------------------------------
# Exception handler registrations
# ---------------------------------------------------------------------------

def _build_error_response(
    status_code: int,
    detail: str | list,
    error_type: str = "error",
) -> JSONResponse:
    """Return a uniform JSON error envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error_type": error_type,
            "detail": detail,
        },
    )


async def http_exception_handler(
    _request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle all HTTPException subclasses (including our custom ones)."""
    return _build_error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        error_type="http_error",
    )


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return a 422 with structured validation error details."""
    errors = []
    for err in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return _build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=errors,
        error_type="validation_error",
    )


async def generic_exception_handler(
    _request: Request,
    _exc: Exception,
) -> JSONResponse:
    """Catch-all for unhandled exceptions — never leak stack traces."""
    return _build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
        error_type="server_error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach all custom exception handlers to the FastAPI application.

    Call this once during app startup (e.g. in ``create_app()``).
    """
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)
