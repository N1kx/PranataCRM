import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.companies.base import CompaniesTestCase
from tests.companies.test_companies import _fake_company


class OwnerReferenceTests(CompaniesTestCase):
    """owner_id on a company must reference a real user in the caller's
    tenant — not just be a syntactically valid UUID."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()
        self._company_id = uuid.uuid4()
        self._owner_id = uuid.uuid4()

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

    @patch("app.modules.companies.repository.CompanyRepository.create", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_create_company_with_existing_owner_id_succeeds(
        self, mock_user_exists, mock_company_create,
    ):
        mock_user_exists.return_value = True
        mock_company_create.return_value = _fake_company(
            self._company_id, self._tenant_id, owner_id=self._owner_id,
        )
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={
                    "name": "Acme Corp", "phone": "+62 812-0000-0000", "country": "ID",
                    "owner_id": str(self._owner_id),
                },
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_user_exists.assert_called_once_with(self._tenant_id, self._owner_id)
        mock_company_create.assert_called_once()

    @patch("app.modules.companies.repository.CompanyRepository.create", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_create_company_with_nonexistent_owner_id_returns_422(
        self, mock_user_exists, mock_company_create,
    ):
        mock_user_exists.return_value = False
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={
                    "name": "Acme Corp", "phone": "+62 812-0000-0000", "country": "ID",
                    "owner_id": str(self._owner_id),
                },
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_OWNER_REFERENCE")
        mock_company_create.assert_not_called()

    @patch("app.modules.companies.repository.CompanyRepository.create", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_create_company_without_owner_id_skips_validation(
        self, mock_user_exists, mock_company_create,
    ):
        mock_company_create.return_value = _fake_company(self._company_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme Corp", "phone": "+62 812-0000-0000", "country": "ID"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_user_exists.assert_not_called()

    # ── update ────────────────────────────────────────────────────────────────

    @patch("app.modules.companies.repository.CompanyRepository.update", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_update_company_with_existing_owner_id_succeeds(
        self, mock_user_exists, mock_get_by_id, mock_update,
    ):
        mock_user_exists.return_value = True
        existing = _fake_company(self._company_id, self._tenant_id)
        mock_get_by_id.return_value = existing
        mock_update.return_value = _fake_company(
            self._company_id, self._tenant_id, owner_id=self._owner_id,
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}",
                json={"owner_id": str(self._owner_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_user_exists.assert_called_once_with(self._tenant_id, self._owner_id)

    @patch("app.modules.companies.repository.CompanyRepository.update", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_update_company_with_nonexistent_owner_id_returns_422(
        self, mock_user_exists, mock_get_by_id, mock_update,
    ):
        mock_user_exists.return_value = False
        mock_get_by_id.return_value = _fake_company(self._company_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}",
                json={"owner_id": str(self._owner_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_OWNER_REFERENCE")
        mock_update.assert_not_called()

    @patch("app.modules.companies.repository.CompanyRepository.update", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_update_company_without_owner_id_skips_validation(
        self, mock_user_exists, mock_get_by_id, mock_update,
    ):
        mock_get_by_id.return_value = _fake_company(self._company_id, self._tenant_id)
        mock_update.return_value = _fake_company(self._company_id, self._tenant_id, name="Renamed")
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}",
                json={"name": "Renamed"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_user_exists.assert_not_called()
