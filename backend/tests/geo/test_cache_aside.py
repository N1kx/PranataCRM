"""Unit tests for GeoService's cache-aside read path and write-through
invalidation (issue #26's Redis caching strategy). GeoRepository and GeoCache
are both mocked — no real DB or Redis needed.
"""
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.modules.geo.exceptions import InvalidCountryReference, InvalidStateReference
from app.modules.geo.schemas import GeoStateCreate, GeoStateUpdate
from app.modules.geo.service import GeoService


def _country(code="ID", name_en="Indonesia"):
    return SimpleNamespace(code=code, name_en=name_en, name_id=None, is_active=True)


def _state(country_code="ID", name="Jawa Barat", state_id=None):
    return SimpleNamespace(
        id=state_id or uuid.uuid4(), country_code=country_code, name=name, code=None, is_active=True,
    )


class CacheAsideTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repo = AsyncMock()
        self.cache = AsyncMock()
        self.service = GeoService(self.repo, self.cache)

    async def test_list_countries_hits_cache_and_skips_db_on_hit(self) -> None:
        self.cache.get_countries.return_value = [
            {"code": "ID", "name_en": "Indonesia", "name_id": None, "is_active": True}
        ]
        result = await self.service.list_countries()
        self.assertEqual(result[0].code, "ID")
        self.repo.list_active_countries.assert_not_called()

    async def test_list_countries_populates_cache_on_miss(self) -> None:
        self.cache.get_countries.return_value = None
        self.repo.list_active_countries.return_value = [_country()]
        result = await self.service.list_countries()
        self.assertEqual(result[0].code, "ID")
        self.cache.set_countries.assert_awaited_once()

    async def test_list_states_rejects_unknown_country_without_hitting_states_cache(self) -> None:
        self.cache.get_countries.return_value = []  # empty but present -> no DB hit, "ID" unknown
        with self.assertRaises(InvalidCountryReference):
            await self.service.list_states("ID")
        self.cache.get_states.assert_not_called()

    async def test_list_states_uses_cache_on_hit(self) -> None:
        self.cache.get_countries.return_value = [
            {"code": "ID", "name_en": "Indonesia", "name_id": None, "is_active": True}
        ]
        self.cache.get_states.return_value = [
            {"id": "s1", "country_code": "ID", "name": "Jawa Barat", "code": None, "is_active": True}
        ]
        result = await self.service.list_states("id")  # lower-case input, normalized to ID
        self.assertEqual(result[0].name, "Jawa Barat")
        self.repo.list_active_states.assert_not_called()

    async def test_create_state_invalidates_only_that_countrys_key(self) -> None:
        self.cache.get_countries.return_value = [
            {"code": "ID", "name_en": "Indonesia", "name_id": None, "is_active": True}
        ]
        self.repo.list_active_states.return_value = []
        new_state = _state()
        self.repo.create_state.return_value = new_state
        await self.service.create_state(GeoStateCreate(country_code="id", name="Jawa Barat"))
        self.cache.invalidate_states.assert_awaited_once_with("ID")

    async def test_update_state_invalidates_states_key_for_states_country(self) -> None:
        state = _state(country_code="ID")
        self.repo.get_state.return_value = state
        self.repo.update_state.return_value = state
        await self.service.update_state(state.id, GeoStateUpdate(name="Renamed"))
        self.cache.invalidate_states.assert_awaited_once_with("ID")

    async def test_delete_state_invalidates_states_key(self) -> None:
        state = _state(country_code="ID")
        self.repo.get_state.return_value = state
        await self.service.delete_state(state.id)
        self.repo.delete_state.assert_awaited_once_with(state)
        self.cache.invalidate_states.assert_awaited_once_with("ID")

    async def test_list_cities_rejects_unknown_or_inactive_state(self) -> None:
        self.repo.get_state.return_value = None
        with self.assertRaises(InvalidStateReference):
            await self.service.list_cities(uuid.uuid4())
        self.cache.get_cities.assert_not_called()

    async def test_create_city_invalidates_cities_key_for_its_state(self) -> None:
        state = _state()
        self.repo.get_state.return_value = state
        self.repo.list_active_cities.return_value = []
        self.repo.create_city.return_value = SimpleNamespace(
            id=uuid.uuid4(), state_id=state.id, country_code="ID", name="Bandung", is_active=True,
        )
        from app.modules.geo.schemas import GeoCityCreate

        await self.service.create_city(GeoCityCreate(state_id=str(state.id), name="Bandung"))
        self.cache.invalidate_cities.assert_awaited_once_with(state.id)


if __name__ == "__main__":
    unittest.main()
