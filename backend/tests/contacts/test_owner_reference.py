import uuid
from unittest.mock import AsyncMock, patch

from tests.contacts.base import ContactsTestCase
from tests.contacts.test_contacts import _fake_contact


class OwnerReferenceTests(ContactsTestCase):
    """owner_id on a contact must reference a real user in the caller's
    tenant — not just be a syntactically valid UUID."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()
        self._contact_id = uuid.uuid4()
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

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_create_contact_with_existing_owner_id_succeeds(
        self, mock_user_exists, mock_contact_create,
    ):
        mock_user_exists.return_value = True
        mock_contact_create.return_value = _fake_contact(
            self._contact_id, self._tenant_id, owner_id=self._owner_id,
        )
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts",
                json={"first_name": "Ada", "owner_id": str(self._owner_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_user_exists.assert_called_once_with(self._tenant_id, self._owner_id)
        mock_contact_create.assert_called_once()

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_create_contact_with_nonexistent_owner_id_returns_422(
        self, mock_user_exists, mock_contact_create,
    ):
        mock_user_exists.return_value = False
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts",
                json={"first_name": "Ada", "owner_id": str(self._owner_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_OWNER_REFERENCE")
        mock_contact_create.assert_not_called()

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_create_contact_without_owner_id_skips_validation(
        self, mock_user_exists, mock_contact_create,
    ):
        mock_contact_create.return_value = _fake_contact(self._contact_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts", json={"first_name": "Ada"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_user_exists.assert_not_called()

    # ── update ────────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_update_contact_with_existing_owner_id_succeeds(
        self, mock_user_exists, mock_get_by_id, mock_update,
    ):
        mock_user_exists.return_value = True
        mock_get_by_id.return_value = _fake_contact(self._contact_id, self._tenant_id)
        mock_update.return_value = _fake_contact(
            self._contact_id, self._tenant_id, owner_id=self._owner_id,
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}",
                json={"owner_id": str(self._owner_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_user_exists.assert_called_once_with(self._tenant_id, self._owner_id)

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_update_contact_with_nonexistent_owner_id_returns_422(
        self, mock_user_exists, mock_get_by_id, mock_update,
    ):
        mock_user_exists.return_value = False
        mock_get_by_id.return_value = _fake_contact(self._contact_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}",
                json={"owner_id": str(self._owner_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_OWNER_REFERENCE")
        mock_update.assert_not_called()

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_update_contact_without_owner_id_skips_validation(
        self, mock_user_exists, mock_get_by_id, mock_update,
    ):
        mock_get_by_id.return_value = _fake_contact(self._contact_id, self._tenant_id)
        mock_update.return_value = _fake_contact(
            self._contact_id, self._tenant_id, first_name="Renamed",
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}",
                json={"first_name": "Renamed"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_user_exists.assert_not_called()

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.user_exists_in_tenant", new_callable=AsyncMock)
    async def test_update_contact_clearing_owner_id_skips_validation(
        self, mock_user_exists, mock_get_by_id, mock_update,
    ):
        mock_get_by_id.return_value = _fake_contact(
            self._contact_id, self._tenant_id, owner_id=self._owner_id,
        )
        mock_update.return_value = _fake_contact(self._contact_id, self._tenant_id, owner_id=None)
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}",
                json={"owner_id": None},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_user_exists.assert_not_called()
