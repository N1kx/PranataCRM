from unittest.mock import AsyncMock, patch

from tests.common import MockedAppTestCase


class ContactsTestCase(MockedAppTestCase):
    """Base for async contacts tests. Redis and DB are mocked.

    country/state/city are validated via GeoContractProtocol on every
    create/update (issue #26); default that to a no-op here so tests
    unrelated to location validation don't need to know about it. Tests that
    specifically exercise geo reference validation (see
    tests/contacts/test_location_reference.py) override this per-test.
    """

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._geo_patcher = patch(
            "app.modules.geo.use_case.GeoUseCase.validate_location",
            new_callable=AsyncMock,
            return_value=None,
        )
        self._geo_patcher.start()

    async def asyncTearDown(self) -> None:
        self._geo_patcher.stop()
        await super().asyncTearDown()
