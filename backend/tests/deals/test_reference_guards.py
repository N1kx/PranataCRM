import uuid
from unittest.mock import AsyncMock, patch

from tests.deals.base import DealsTestCase
from tests.deals.test_deals import _fake_deal


class ReferenceGuardTests(DealsTestCase):
    """contact_id/company_id/owner_id on a deal must reference a real
    contact/company/user in the caller's tenant — not just be a
    syntactically valid UUID (ADR-005 write guard)."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()
        self._deal_id = uuid.uuid4()
        self._owner_id = uuid.uuid4()
        self._company_id = uuid.uuid4()
        self._contact_id = uuid.uuid4()

    def _override_current_user(self):
        from app.main import app
        from app.modules.auth.dependencies import CurrentUser, get_current_user

        async def _override():
            return CurrentUser(
                user_id=self._user_id, tenant_id=self._tenant_id, suite_role="tenant_owner"
            )

        app.dependency_overrides[get_current_user] = _override
        return app

    def _clear_override(self, app):
        from app.modules.auth.dependencies import get_current_user
        app.dependency_overrides.pop(get_current_user, None)

    # ── create ────────────────────────────────────────────────────────────────

    @patch("app.modules.deals.repository.DealRepository.create", new_callable=AsyncMock)
    @patch("app.modules.auth.use_case.AuthUseCase.user_exists", new_callable=AsyncMock)
    async def test_create_deal_with_nonexistent_owner_id_returns_422(
        self, mock_user_exists, mock_create,
    ):
        mock_user_exists.return_value = False
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/deals",
                json={
                    "title": "Big Sale", "expected_close_date": "2026-12-31",
                    "owner_id": str(self._owner_id),
                },
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_OWNER_REFERENCE")
        mock_create.assert_not_called()

    @patch("app.modules.deals.repository.DealRepository.create", new_callable=AsyncMock)
    @patch("app.modules.companies.use_case.CompanyUseCase.company_exists", new_callable=AsyncMock)
    async def test_create_deal_with_nonexistent_company_id_returns_422(
        self, mock_company_exists, mock_create,
    ):
        mock_company_exists.return_value = False
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/deals",
                json={
                    "title": "Big Sale", "expected_close_date": "2026-12-31",
                    "company_id": str(self._company_id),
                },
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_COMPANY_REFERENCE")
        mock_create.assert_not_called()

    @patch("app.modules.deals.repository.DealRepository.create", new_callable=AsyncMock)
    @patch("app.modules.contacts.use_case.ContactUseCase.contact_exists", new_callable=AsyncMock)
    async def test_create_deal_with_nonexistent_contact_id_returns_422(
        self, mock_contact_exists, mock_create,
    ):
        mock_contact_exists.return_value = False
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/deals",
                json={
                    "title": "Big Sale", "expected_close_date": "2026-12-31",
                    "contact_id": str(self._contact_id),
                },
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_CONTACT_REFERENCE")
        mock_create.assert_not_called()

    @patch("app.modules.deals.repository.DealRepository.create", new_callable=AsyncMock)
    @patch("app.modules.auth.use_case.AuthUseCase.user_exists", new_callable=AsyncMock)
    async def test_create_deal_without_references_skips_validation(
        self, mock_user_exists, mock_create,
    ):
        mock_create.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/deals",
                json={"title": "Big Sale", "expected_close_date": "2026-12-31"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_user_exists.assert_not_called()

    # ── update ────────────────────────────────────────────────────────────────

    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.auth.use_case.AuthUseCase.user_exists", new_callable=AsyncMock)
    async def test_update_deal_with_nonexistent_owner_id_returns_422(
        self, mock_user_exists, mock_get,
    ):
        mock_user_exists.return_value = False
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}",
                json={"owner_id": str(self._owner_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_OWNER_REFERENCE")

    @patch("app.modules.deals.repository.DealRepository.update", new_callable=AsyncMock)
    @patch("app.modules.deals.repository.DealRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_deal_without_references_skips_validation(
        self, mock_get, mock_update,
    ):
        mock_get.return_value = _fake_deal(self._deal_id, self._tenant_id)
        mock_update.return_value = _fake_deal(self._deal_id, self._tenant_id, title="Renamed")
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/deals/{self._deal_id}", json={"title": "Renamed"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
