import uuid

from app.modules.geo.cache import GeoCache
from app.modules.geo.exceptions import (
    CityNotFound,
    CountryNotFound,
    GeoValidationError,
    InvalidCountryReference,
    InvalidStateReference,
    StateNotFound,
)
from app.modules.geo.models import GeoCity, GeoCountry, GeoState
from app.modules.geo.repository import GeoRepository
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


class GeoService:
    """Internal domain logic for geo reference data. Never imported from
    outside this module. Owns the cache-aside read path and write-through
    invalidation described in issue #26."""

    def __init__(self, repo: GeoRepository, cache: GeoCache) -> None:
        self._repo = repo
        self._cache = cache

    # ── read path (cache-aside, feeds both the public API and cross-module
    #    reference validation used by contacts/companies) ────────────────────

    async def _country_map(self) -> dict[str, dict]:
        cached = await self._cache.get_countries()
        if cached is None:
            rows = await self._repo.list_active_countries()
            cached = [self._country_to_dict(c) for c in rows]
            await self._cache.set_countries(cached)
        return {c["code"]: c for c in cached}

    async def list_countries(self) -> list[GeoCountryResponse]:
        m = await self._country_map()
        return [GeoCountryResponse(**c) for c in m.values()]

    async def country_exists(self, country_code: str) -> bool:
        return country_code.upper() in await self._country_map()

    async def _state_map(self, country_code: str) -> dict[str, dict]:
        country_code = country_code.upper()
        cached = await self._cache.get_states(country_code)
        if cached is None:
            rows = await self._repo.list_active_states(country_code)
            cached = [self._state_to_dict(s) for s in rows]
            await self._cache.set_states(country_code, cached)
        return {s["id"]: s for s in cached}

    async def list_states(self, country_code: str) -> list[GeoStateResponse]:
        if not await self.country_exists(country_code):
            raise InvalidCountryReference()
        m = await self._state_map(country_code)
        return [GeoStateResponse(**s) for s in m.values()]

    async def state_exists(self, country_code: str, state_id: uuid.UUID) -> bool:
        m = await self._state_map(country_code)
        return str(state_id) in m

    async def _city_map(self, state_id: uuid.UUID) -> dict[str, dict]:
        cached = await self._cache.get_cities(state_id)
        if cached is None:
            rows = await self._repo.list_active_cities(state_id)
            cached = [self._city_to_dict(c) for c in rows]
            await self._cache.set_cities(state_id, cached)
        return {c["id"]: c for c in cached}

    async def list_cities(self, state_id: uuid.UUID) -> list[GeoCityResponse]:
        state = await self._repo.get_state(state_id)
        if state is None or not state.is_active:
            raise InvalidStateReference()
        m = await self._city_map(state_id)
        return [GeoCityResponse(**c) for c in m.values()]

    async def city_exists(self, state_id: uuid.UUID, city_id: uuid.UUID) -> bool:
        m = await self._city_map(state_id)
        return str(city_id) in m

    # ── admin writes (write-through invalidation: precise, never a global
    #    flush — see GeoCache module docstring) ──────────────────────────────

    async def update_country(self, code: str, payload: GeoCountryUpdate) -> GeoCountryResponse:
        country = await self._repo.get_country(code)
        if country is None:
            raise CountryNotFound()
        data = payload.model_dump(exclude_unset=True)
        country = await self._repo.update_country(country, data)
        await self._cache.invalidate_countries()
        return GeoCountryResponse(**self._country_to_dict(country))

    async def create_state(self, payload: GeoStateCreate) -> GeoStateResponse:
        if not await self.country_exists(payload.country_code):
            raise InvalidCountryReference()
        existing = await self._repo.list_active_states(payload.country_code)
        if any(s.name.lower() == payload.name.lower() for s in existing):
            raise GeoValidationError(
                f"A state named '{payload.name}' already exists for country "
                f"{payload.country_code}."
            )
        state = await self._repo.create_state(
            {
                "country_code": payload.country_code,
                "name": payload.name,
                "code": payload.code,
            }
        )
        await self._cache.invalidate_states(payload.country_code)
        return GeoStateResponse(**self._state_to_dict(state))

    async def update_state(self, state_id: uuid.UUID, payload: GeoStateUpdate) -> GeoStateResponse:
        state = await self._repo.get_state(state_id)
        if state is None:
            raise StateNotFound()
        data = payload.model_dump(exclude_unset=True)
        state = await self._repo.update_state(state, data)
        await self._cache.invalidate_states(state.country_code)
        return GeoStateResponse(**self._state_to_dict(state))

    async def delete_state(self, state_id: uuid.UUID) -> None:
        state = await self._repo.get_state(state_id)
        if state is None:
            raise StateNotFound()
        country_code = state.country_code
        await self._repo.delete_state(state)
        await self._cache.invalidate_states(country_code)

    async def create_city(self, payload: GeoCityCreate) -> GeoCityResponse:
        state = await self._repo.get_state(uuid.UUID(payload.state_id))
        if state is None:
            raise InvalidStateReference()
        existing = await self._repo.list_active_cities(state.id)
        if any(c.name.lower() == payload.name.lower() for c in existing):
            raise GeoValidationError(
                f"A city named '{payload.name}' already exists for state {state.name}."
            )
        city = await self._repo.create_city(
            {
                "state_id": state.id,
                "country_code": state.country_code,
                "name": payload.name,
            }
        )
        await self._cache.invalidate_cities(state.id)
        return GeoCityResponse(**self._city_to_dict(city))

    async def update_city(self, city_id: uuid.UUID, payload: GeoCityUpdate) -> GeoCityResponse:
        city = await self._repo.get_city(city_id)
        if city is None:
            raise CityNotFound()
        data = payload.model_dump(exclude_unset=True)
        city = await self._repo.update_city(city, data)
        await self._cache.invalidate_cities(city.state_id)
        return GeoCityResponse(**self._city_to_dict(city))

    async def delete_city(self, city_id: uuid.UUID) -> None:
        city = await self._repo.get_city(city_id)
        if city is None:
            raise CityNotFound()
        state_id = city.state_id
        await self._repo.delete_city(city)
        await self._cache.invalidate_cities(state_id)

    # ── mappers (also define the JSON shape stored in Redis) ────────────────

    @staticmethod
    def _country_to_dict(c: GeoCountry) -> dict:
        return {"code": c.code, "name_en": c.name_en, "name_id": c.name_id, "is_active": c.is_active}

    @staticmethod
    def _state_to_dict(s: GeoState) -> dict:
        return {
            "id": str(s.id),
            "country_code": s.country_code,
            "name": s.name,
            "code": s.code,
            "is_active": s.is_active,
        }

    @staticmethod
    def _city_to_dict(c: GeoCity) -> dict:
        return {
            "id": str(c.id),
            "state_id": str(c.state_id),
            "country_code": c.country_code,
            "name": c.name,
            "is_active": c.is_active,
        }
