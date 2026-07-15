import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.contacts.base import ContactsTestCase
from tests.contacts.test_contacts import _fake_contact


def _fake_company(company_id: uuid.UUID, tenant_id: uuid.UUID) -> SimpleNamespace:
    return SimpleNamespace(
        id=company_id,
        tenant_id=tenant_id,
        name="Acme Corp",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class CompanyReferenceTests(ContactsTestCase):
    """company_id on a contact must reference a real company in the caller's
    tenant — not just be a syntactically valid UUID."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()
        self._contact_id = uuid.uuid4()
        self._company_id = uuid.uuid4()

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

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_create_contact_with_existing_company_id_succeeds(
        self, mock_company_get, mock_contact_create,
    ):
        mock_company_get.return_value = _fake_company(self._company_id, self._tenant_id)
        mock_contact_create.return_value = _fake_contact(
            self._contact_id, self._tenant_id, company_id=self._company_id,
        )
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts",
                json={"first_name": "Ada", "company_id": str(self._company_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_company_get.assert_called_once_with(self._tenant_id, self._company_id)
        mock_contact_create.assert_called_once()

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_create_contact_with_nonexistent_company_id_returns_422(
        self, mock_company_get, mock_contact_create,
    ):
        mock_company_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts",
                json={"first_name": "Ada", "company_id": str(self._company_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_COMPANY_REFERENCE")
        mock_contact_create.assert_not_called()

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_create_contact_with_cross_tenant_company_id_returns_422(
        self, mock_company_get, mock_contact_create,
    ):
        # The repository always filters by tenant_id, so a company belonging to
        # another tenant is indistinguishable from a nonexistent one here.
        mock_company_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts",
                json={"first_name": "Ada", "company_id": str(self._company_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        mock_company_get.assert_called_once_with(self._tenant_id, self._company_id)
        mock_contact_create.assert_not_called()

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_create_contact_without_company_id_skips_validation(
        self, mock_company_get, mock_contact_create,
    ):
        mock_contact_create.return_value = _fake_contact(self._contact_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.post("/api/v1/contacts", json={"first_name": "Ada"})
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_company_get.assert_not_called()

    # ── update ────────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_contact_with_existing_company_id_succeeds(
        self, mock_company_get, mock_contact_get, mock_contact_update,
    ):
        mock_company_get.return_value = _fake_company(self._company_id, self._tenant_id)
        mock_contact_get.return_value = _fake_contact(self._contact_id, self._tenant_id)
        mock_contact_update.return_value = _fake_contact(
            self._contact_id, self._tenant_id, company_id=self._company_id,
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}",
                json={"company_id": str(self._company_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_company_get.assert_called_once_with(self._tenant_id, self._company_id)

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_contact_with_nonexistent_company_id_returns_422(
        self, mock_company_get, mock_contact_get, mock_contact_update,
    ):
        mock_company_get.return_value = None
        mock_contact_get.return_value = _fake_contact(self._contact_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}",
                json={"company_id": str(self._company_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_COMPANY_REFERENCE")
        mock_contact_update.assert_not_called()

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_contact_clearing_company_id_skips_validation(
        self, mock_company_get, mock_contact_get, mock_contact_update,
    ):
        # Sending company_id: null unassigns the company - this must NOT be
        # treated as an invalid reference, since it doesn't reference anything.
        mock_contact_get.return_value = _fake_contact(
            self._contact_id, self._tenant_id, company_id=self._company_id,
        )
        mock_contact_update.return_value = _fake_contact(
            self._contact_id, self._tenant_id, company_id=None,
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}", json={"company_id": None},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_company_get.assert_not_called()

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_contact_without_company_id_skips_validation(
        self, mock_company_get, mock_contact_get, mock_contact_update,
    ):
        # Partial update that never mentions company_id at all.
        mock_contact_get.return_value = _fake_contact(self._contact_id, self._tenant_id)
        mock_contact_update.return_value = _fake_contact(
            self._contact_id, self._tenant_id, job_title="Engineer",
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}", json={"job_title": "Engineer"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_company_get.assert_not_called()
