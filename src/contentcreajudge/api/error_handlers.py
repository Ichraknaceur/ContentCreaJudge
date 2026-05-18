"""Centralized API exception handlers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from contentcreajudge.core.error_models import ErrorDetails, ErrorResponse
from contentcreajudge.core.errors import ContentCreaJudgeError

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)


def _build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetails(
            code=code,
            message=message,
            details=details,
        ),
        request_id=request_id,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_error_handlers(application: FastAPI) -> None:
    """Register all shared API exception handlers on the FastAPI app."""

    @application.exception_handler(ContentCreaJudgeError)
    async def handle_application_error(
        request: Request,
        exc: ContentCreaJudgeError,
    ) -> JSONResponse:
        return _build_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=getattr(request.state, "request_id", None),
        )

    @application.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _build_error_response(
            status_code=422,
            code="request_validation_error",
            message="Request payload validation failed.",
            details={"errors": exc.errors()},
            request_id=getattr(request.state, "request_id", None),
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled exception while processing request.", exc_info=exc)
        return _build_error_response(
            status_code=500,
            code="internal_server_error",
            message="An unexpected internal server error occurred.",
            request_id=getattr(request.state, "request_id", None),
        )
