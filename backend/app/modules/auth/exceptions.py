from fastapi import status

from app.shared.exceptions import AppException


class EmailAlreadyExists(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "AUTH_EMAIL_EXISTS"
    message = "This email is already registered in this organization."


class SlugAlreadyTaken(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "AUTH_SLUG_TAKEN"
    message = "This workspace address is already taken."


class InvalidCredentials(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTH_INVALID_CREDENTIALS"
    message = "Incorrect email or password."


class TenantNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "AUTH_TENANT_NOT_FOUND"
    message = "Workspace not found."


class NotAuthenticated(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTH_NOT_AUTHENTICATED"
    message = "You are not signed in."


class SeatLimitReached(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "AUTH_SEAT_LIMIT"
    message = "Seat quota is full. Add more seats to invite additional users."


class InviteInvalidOrExpired(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "AUTH_INVITE_INVALID"
    message = "The invitation is invalid or has expired."


class PermissionDenied(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "AUTH_PERMISSION_DENIED"
    message = "You do not have permission for this action."
