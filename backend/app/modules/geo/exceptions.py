from fastapi import status

from app.shared.exceptions import AppException


class InvalidCountryReference(AppException):
    # 422, not 404: the client sent a syntactically-valid country code, but it
    # doesn't resolve to a known, active ISO 3166-1 country — a request
    # validation problem, the same class of error as a bad enum value.
    status_code = 422
    error_code = "INVALID_COUNTRY_REFERENCE"
    message = "country does not reference a known, active country code."


class InvalidStateReference(AppException):
    # 422: state exists but doesn't belong to the given country, or doesn't
    # exist/isn't active at all.
    status_code = 422
    error_code = "INVALID_STATE_REFERENCE"
    message = "state does not reference an active state belonging to the given country."


class InvalidCityReference(AppException):
    status_code = 422
    error_code = "INVALID_CITY_REFERENCE"
    message = "city does not reference an active city belonging to the given state."


class CountryNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "COUNTRY_NOT_FOUND"
    message = "Country not found."


class StateNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "STATE_NOT_FOUND"
    message = "State not found."


class CityNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "CITY_NOT_FOUND"
    message = "City not found."


class GeoValidationError(AppException):
    """Malformed/inconsistent geo input that isn't a specific reference error:
    missing required query param, cascade-completeness violation (state
    without country, city without state), or a duplicate name on admin
    create/update. Same {"error": {code, message, detail}} envelope as every
    other AppException — never FastAPI's default {"detail": [...]} shape.
    """
    status_code = 422
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()
