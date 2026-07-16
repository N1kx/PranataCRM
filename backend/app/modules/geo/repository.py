from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.geo.exceptions import GeoValidationError
from app.modules.geo.models import GeoCity, GeoCountry, GeoState


class GeoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── countries ─────────────────────────────────────────────────────────────

    async def list_active_countries(self) -> list[GeoCountry]:
        result = await self._session.execute(
            select(GeoCountry).where(GeoCountry.is_active.is_(True)).order_by(GeoCountry.name_en)
        )
        return list(result.scalars().all())

    async def get_country(self, code: str) -> GeoCountry | None:
        result = await self._session.execute(
            select(GeoCountry).where(GeoCountry.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def update_country(self, country: GeoCountry, data: dict) -> GeoCountry:
        for key, value in data.items():
            setattr(country, key, value)
        await self._session.flush()
        return country

    # ── states ────────────────────────────────────────────────────────────────

    async def list_active_states(self, country_code: str) -> list[GeoState]:
        result = await self._session.execute(
            select(GeoState)
            .where(GeoState.country_code == country_code.upper(), GeoState.is_active.is_(True))
            .order_by(GeoState.name)
        )
        return list(result.scalars().all())

    async def get_state(self, state_id: uuid.UUID) -> GeoState | None:
        result = await self._session.execute(select(GeoState).where(GeoState.id == state_id))
        return result.scalar_one_or_none()

    async def create_state(self, data: dict) -> GeoState:
        state = GeoState(**data)
        self._session.add(state)
        try:
            await self._session.flush()
        except IntegrityError:
            # GeoService's own pre-check only looks at *active* rows, so a
            # name collision with a deactivated state (or a concurrent
            # request) reaches the DB's uq_geo_states_country_name
            # constraint instead — translate it to a clean 422 rather than
            # letting an aborted-transaction IntegrityError bubble up as a
            # 500 (and poison the request's session for the router's
            # trailing commit).
            await self._session.rollback()
            raise GeoValidationError(
                f"A state named '{data.get('name')}' already exists for country "
                f"{data.get('country_code')}."
            )
        return state

    async def update_state(self, state: GeoState, data: dict) -> GeoState:
        for key, value in data.items():
            setattr(state, key, value)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise GeoValidationError(
                f"A state named '{data.get('name', state.name)}' already exists "
                f"for this country."
            )
        return state

    async def delete_state(self, state: GeoState) -> None:
        await self._session.delete(state)
        await self._session.flush()

    # ── cities ────────────────────────────────────────────────────────────────

    async def list_active_cities(self, state_id: uuid.UUID) -> list[GeoCity]:
        result = await self._session.execute(
            select(GeoCity)
            .where(GeoCity.state_id == state_id, GeoCity.is_active.is_(True))
            .order_by(GeoCity.name)
        )
        return list(result.scalars().all())

    async def get_city(self, city_id: uuid.UUID) -> GeoCity | None:
        result = await self._session.execute(select(GeoCity).where(GeoCity.id == city_id))
        return result.scalar_one_or_none()

    async def create_city(self, data: dict) -> GeoCity:
        city = GeoCity(**data)
        self._session.add(city)
        try:
            await self._session.flush()
        except IntegrityError:
            # See create_state's comment — same TOCTOU/inactive-row gap for
            # uq_geo_cities_state_name.
            await self._session.rollback()
            raise GeoValidationError(
                f"A city named '{data.get('name')}' already exists for this state."
            )
        return city

    async def update_city(self, city: GeoCity, data: dict) -> GeoCity:
        for key, value in data.items():
            setattr(city, key, value)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise GeoValidationError(
                f"A city named '{data.get('name', city.name)}' already exists "
                f"for this state."
            )
        return city

    async def delete_city(self, city: GeoCity) -> None:
        await self._session.delete(city)
        await self._session.flush()
