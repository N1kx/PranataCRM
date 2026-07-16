"""Pure unit tests for GeoUseCase.validate_location — the cascade-completeness
and cross-parent reference rules from issue #26. No HTTP, no DB, no Redis:
GeoService is mocked so this exercises only the use_case's own logic.
"""
import unittest
import uuid
from unittest.mock import AsyncMock

from app.modules.geo.exceptions import (
    GeoValidationError,
    InvalidCityReference,
    InvalidCountryReference,
    InvalidStateReference,
)
from app.modules.geo.use_case import GeoUseCase


class ValidateLocationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.service = AsyncMock()
        self.use_case = GeoUseCase(self.service)
        self.state_id = uuid.uuid4()
        self.city_id = uuid.uuid4()

    async def test_all_none_is_a_noop(self) -> None:
        await self.use_case.validate_location(None, None, None)
        self.service.country_exists.assert_not_called()
        self.service.state_exists.assert_not_called()
        self.service.city_exists.assert_not_called()

    async def test_country_only_validates_country(self) -> None:
        self.service.country_exists.return_value = True
        await self.use_case.validate_location("ID", None, None)
        self.service.country_exists.assert_awaited_once_with("ID")
        self.service.state_exists.assert_not_called()

    async def test_unknown_country_raises_invalid_country_reference(self) -> None:
        self.service.country_exists.return_value = False
        with self.assertRaises(InvalidCountryReference):
            await self.use_case.validate_location("ZZ", None, None)

    async def test_state_without_country_raises_cascade_error(self) -> None:
        with self.assertRaises(GeoValidationError):
            await self.use_case.validate_location(None, self.state_id, None)
        self.service.country_exists.assert_not_called()

    async def test_city_without_state_raises_cascade_error(self) -> None:
        with self.assertRaises(GeoValidationError):
            await self.use_case.validate_location("ID", None, self.city_id)
        self.service.state_exists.assert_not_called()

    async def test_valid_country_and_state_succeeds(self) -> None:
        self.service.country_exists.return_value = True
        self.service.state_exists.return_value = True
        await self.use_case.validate_location("ID", self.state_id, None)
        self.service.state_exists.assert_awaited_once_with("ID", self.state_id)

    async def test_state_not_belonging_to_country_raises_invalid_state_reference(self) -> None:
        self.service.country_exists.return_value = True
        self.service.state_exists.return_value = False
        with self.assertRaises(InvalidStateReference):
            await self.use_case.validate_location("ID", self.state_id, None)

    async def test_valid_full_cascade_succeeds(self) -> None:
        self.service.country_exists.return_value = True
        self.service.state_exists.return_value = True
        self.service.city_exists.return_value = True
        await self.use_case.validate_location("ID", self.state_id, self.city_id)
        self.service.city_exists.assert_awaited_once_with(self.state_id, self.city_id)

    async def test_city_not_belonging_to_state_raises_invalid_city_reference(self) -> None:
        self.service.country_exists.return_value = True
        self.service.state_exists.return_value = True
        self.service.city_exists.return_value = False
        with self.assertRaises(InvalidCityReference):
            await self.use_case.validate_location("ID", self.state_id, self.city_id)

    async def test_invalid_country_short_circuits_before_state_check(self) -> None:
        self.service.country_exists.return_value = False
        with self.assertRaises(InvalidCountryReference):
            await self.use_case.validate_location("ID", self.state_id, self.city_id)
        self.service.state_exists.assert_not_called()
        self.service.city_exists.assert_not_called()


if __name__ == "__main__":
    unittest.main()
