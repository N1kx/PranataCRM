from fastapi import status

from app.shared.exceptions import AppException


class ContactNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "CONTACT_NOT_FOUND"
    message = "Contact not found."


class InvalidCompanyReference(AppException):
    # 422, not 404: the client sent a syntactically-valid company_id, but it
    # doesn't resolve to a real company in the caller's tenant — a request
    # validation problem, the same class of error as a bad enum value.
    status_code = 422
    error_code = "INVALID_COMPANY_REFERENCE"
    message = "company_id does not reference an existing company."
