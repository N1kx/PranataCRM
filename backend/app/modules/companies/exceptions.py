from fastapi import status

from app.shared.exceptions import AppException


class CompanyNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "COMPANY_NOT_FOUND"
    message = "Company not found."


class CompanyQueryValidationError(AppException):
    """Invalid GET /companies query parameter (e.g. bad enum, UUID, or sort field).

    Raised from the router (not a Pydantic body schema, since these are plain
    query params), but still returns the same {"error": {code, message,
    detail}} shape as every other AppException — never FastAPI's default
    {"detail": [...]} shape, which would be inconsistent with the rest of the API.
    """
    # status.HTTP_422_UNPROCESSABLE_ENTITY is deprecated in newer Starlette in
    # favor of HTTP_422_UNPROCESSABLE_CONTENT; using the stable numeric code
    # avoids depending on either name.
    status_code = 422
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()
