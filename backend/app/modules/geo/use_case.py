import uuid

from app.modules.geo.exceptions import (
    GeoValidationError,
    InvalidCityReference,
    InvalidCountryReference,
    InvalidStateReference,
)
from app.modules.geo.schemas import (
    GeoCityCreate,
    GeoCityResponse,
    GeoCityUpdate,
    GeoCountryResponse,
    GeoCountryUpdate,
    GeoStateCreate,
    GeoStateResponse,
    GeoStateUpdate,
)
from app.modules.geo.service import GeoService


class GeoUseCase:
    """Implements GeoContractProtocol. Entry point for the geo module — both
    its own router and other modules (contacts, companies, ...) call in
    through here, never through GeoService directly."""

    def __init__(self, service: GeoService) -> None:
        self._service = service

    # ── GeoContractProtocol ──────────────────────────────────────────────────

    async def validate_location(
        self,
        country: str | None,
        state: uuid.UUID | None,
        city: uuid.UUID | None,
    ) -> None:
        if state is not None and country is None:
            raise GeoValidationError("state requires country.")
        if city is not None and state is None:
            raise GeoValidationError("city requires state.")

        if country is not None:
            if not await self._service.country_exists(country):
                raise InvalidCountryReference()

        if state is not None:
            # country is guaranteed non-None here (checked above).
            if not await self._service.state_exists(country, state):  # type: ignore[arg-type]
                raise InvalidStateReference()

        if city is not None:
            if not await self._service.city_exists(state, city):  # type: ignore[arg-type]
                raise InvalidCityReference()

    # ── public lookup (feeds the frontend autocompletes) ────────────────────

    async def list_countries(self) -> list[GeoCountryResponse]:
        return await self._service.list_countries()

    async def list_states(self, country_code: str) -> list[GeoStateResponse]:
        return await self._service.list_states(country_code)

    async def list_cities(self, state_id: uuid.UUID) -> list[GeoCityResponse]:
        return await self._service.list_cities(state_id)

    # ── admin CRUD (platform-admin only, gated in the router) ────────────────

    async def update_country(self, code: str, payload: GeoCountryUpdate) -> GeoCountryResponse:
        return await self._service.update_country(code, payload)

    async def create_state(self, payload: GeoStateCreate) -> GeoStateResponse:
        return await self._service.create_state(payload)

    async def update_state(self, state_id: uuid.UUID, payload: GeoStateUpdate) -> GeoStateResponse:
        return await self._service.update_state(state_id, payload)

    async def delete_state(self, state_id: uuid.UUID) -> None:
        await self._service.delete_state(state_id)

    async def create_city(self, payload: GeoCityCreate) -> GeoCityResponse:
        return await self._service.create_city(payload)

    async def update_city(self, city_id: uuid.UUID, payload: GeoCityUpdate) -> GeoCityResponse:
        return await self._service.update_city(city_id, payload)

    async def delete_city(self, city_id: uuid.UUID) -> None:
        await self._service.delete_city(city_id)
