from unittest.mock import AsyncMock, patch

from tests.common import MockedAppTestCase


class DealsTestCase(MockedAppTestCase):
    """Base for async deals tests. Redis and DB are mocked.

    contact_id/company_id/owner_id are validated for existence via their
    respective contracts on every create/update (ADR-005 write guard);
    default all three to a no-op "exists" here so tests unrelated to
    reference validation don't need to know about it. Tests that
    specifically exercise reference validation (see
    tests/deals/test_reference_guards.py) override this per-test.
    """

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._auth_patcher = patch(
            "app.modules.auth.use_case.AuthUseCase.user_exists",
            new_callable=AsyncMock,
            return_value=True,
        )
        self._company_patcher = patch(
            "app.modules.companies.use_case.CompanyUseCase.company_exists",
            new_callable=AsyncMock,
            return_value=True,
        )
        self._contact_patcher = patch(
            "app.modules.contacts.use_case.ContactUseCase.contact_exists",
            new_callable=AsyncMock,
            return_value=True,
        )
        self._auth_patcher.start()
        self._company_patcher.start()
        self._contact_patcher.start()

    async def asyncTearDown(self) -> None:
        self._auth_patcher.stop()
        self._company_patcher.stop()
        self._contact_patcher.stop()
        await super().asyncTearDown()
