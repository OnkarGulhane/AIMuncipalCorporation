from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base application exception with plain-language message and actionable user hints."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        action_hint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.action_hint = action_hint or "Please retry the operation or contact municipal support if the issue persists."
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(AppError):
    def __init__(
        self,
        resource: str,
        identifier: Any,
        action_hint: Optional[str] = "Please verify the identifier or browse the active complaints catalog.",
    ):
        super().__init__(
            message=f"{resource} '{identifier}' was not found in the municipal records.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            action_hint=action_hint,
            details={"resource": resource, "identifier": str(identifier)},
        )


class PermissionDeniedError(AppError):
    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        action_hint: Optional[str] = "Contact your departmental administrator if you require elevated privileges.",
    ):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
            action_hint=action_hint,
        )


class ValidationError(AppError):
    def __init__(
        self,
        message: str,
        action_hint: Optional[str] = "Please correct the highlighted fields and try submitting again.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_FAILED",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            action_hint=action_hint,
            details=details,
        )


class ConflictError(AppError):
    def __init__(
        self,
        message: str,
        action_hint: Optional[str] = "Please review existing records or refresh your view.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="CONFLICT_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            action_hint=action_hint,
            details=details,
        )


def format_error_response(
    code: str,
    message: str,
    action_hint: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "detail": message,
        "error": {
            "code": code,
            "message": message,
            "action_hint": action_hint,
            "details": details or {},
        },
    }



async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=exc.code,
            message=exc.message,
            action_hint=exc.action_hint,
            details=exc.details,
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    action_hint = "Please retry or check the requested URL."
    code = "HTTP_ERROR"
    if exc.status_code == 404:
        code = "RESOURCE_NOT_FOUND"
        action_hint = "The requested resource could not be found. Please verify the link or search for the case."
    elif exc.status_code == 403:
        code = "FORBIDDEN"
        action_hint = "You do not have permission to access this resource."
    elif exc.status_code == 401:
        code = "UNAUTHORIZED"
        action_hint = "Please log in to continue."
    elif exc.status_code == 400:
        code = "BAD_REQUEST"
        action_hint = "Please check your input values and try again."

    # Preserve exc.detail string or dict
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=code,
            message=msg,
            action_hint=action_hint,
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        errors.append({"field": field, "issue": err.get("msg", "Invalid value")})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            code="VALIDATION_FAILED",
            message="Input data validation failed. Please check the submitted fields.",
            action_hint="Ensure all required fields are filled with the correct format.",
            details={"validation_errors": errors},
        ),
    )
