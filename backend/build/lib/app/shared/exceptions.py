from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any


class AppException(Exception):
    def __init__(self, status_code: int, detail: str, errors: list[dict[str, str]] | None = None):
        self.status_code = status_code
        self.detail = detail
        self.errors = errors or []
        super().__init__(detail)


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class ConflictError(AppException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=409, detail=detail)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)


class AuthenticationError(AppException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=401, detail=detail)


class BadRequestError(AppException):
    def __init__(self, detail: str = "Bad request", errors: list[dict[str, str]] | None = None):
        super().__init__(status_code=400, detail=detail, errors=errors)


def _format_error_response(status_code: int, detail: str, errors: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {"detail": detail, "status_code": status_code, "errors": errors or []}


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=_format_error_response(exc.status_code, exc.detail, exc.errors))


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []))
        errors.append({"field": field, "message": err.get("msg", "")})
    return JSONResponse(status_code=422, content=_format_error_response(422, "Validation failed", errors))
