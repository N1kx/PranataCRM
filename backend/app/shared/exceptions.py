from http import HTTPStatus


class AppError(Exception):
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    detail = "Resource not found."


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    detail = "Authentication required."


class ForbiddenError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    detail = "You do not have permission to perform this action."


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    detail = "Resource already exists."


class UnprocessableError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    detail = "Unprocessable input."


class ServiceUnavailableError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    detail = "Downstream service is unavailable."
