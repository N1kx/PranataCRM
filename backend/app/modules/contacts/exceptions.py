from fastapi import status

from app.shared.exceptions import AppException


class ContactNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "CONTACT_NOT_FOUND"
    message = "Contact not found."
