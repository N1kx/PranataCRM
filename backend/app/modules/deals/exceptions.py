from fastapi import status

from app.shared.exceptions import AppException


class DealNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "DEAL_NOT_FOUND"
    message = "Deal not found."


class InvalidOwnerReference(AppException):
    # 422, not 404: the client sent a syntactically-valid owner_id, but it
    # doesn't resolve to a real user in the caller's tenant — a request
    # validation problem, the same class of error as a bad enum value.
    status_code = 422
    error_code = "INVALID_OWNER_REFERENCE"
    message = "owner_id does not reference an existing user."


class InvalidCompanyReference(AppException):
    status_code = 422
    error_code = "INVALID_COMPANY_REFERENCE"
    message = "company_id does not reference an existing company."


class InvalidContactReference(AppException):
    status_code = 422
    error_code = "INVALID_CONTACT_REFERENCE"
    message = "contact_id does not reference an existing contact."


class InvalidStageTransition(AppException):
    """A stage/status change that violates the deal lifecycle rules: a stage
    write through the generic PATCH endpoint, a stage change on an abandoned
    deal, a missing lost_reason on -> lost, or an unsupported status value/
    transition through the generic PATCH endpoint."""
    status_code = 422
    error_code = "INVALID_STAGE_TRANSITION"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()


class DealQueryValidationError(AppException):
    """Invalid GET /deals query parameter (e.g. bad enum, UUID, or sort field).

    Raised from the router (not a Pydantic body schema, since these are plain
    query params), but still returns the same {"error": {code, message,
    detail}} shape as every other AppException — never FastAPI's default
    {"detail": [...]} shape, which would be inconsistent with the rest of the API.
    """
    status_code = 422
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()
