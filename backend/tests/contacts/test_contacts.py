import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.contacts.base import ContactsTestCase


def _fake_contact(
    contact_id: uuid.UUID,
    tenant_id: uuid.UUID,
    first_name: str = "Ada",
    **overrides,
) -> SimpleNamespace:
    defaults = dict(
        id=contact_id,
        tenant_id=tenant_id,
        owner_id=None,
        company_id=None,
        first_name=first_name,
        last_name="Lovelace",
        email="ada@example.com",
        secondary_email=None,
        phone=None,
        mobile_phone=None,
        job_title=None,
        department=None,
        status="lead",
        lifecycle_stage=None,
        lead_source=None,
        linkedin_url=None,
        twitter_handle=None,
        address_line1=None,
        city=None,
        state=None,
        postal_code=None,
        country=None,
        timezone=None,
        preferred_contact_method=None,
        preferred_language=None,
        do_not_contact=False,
        description=None,
        tags=[],
        custom_fields={},
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class ContactsTests(ContactsTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()
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

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    async def test_create_contact_success(self, mock_create):
        mock_create.return_value = _fake_contact(self._contact_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts", json={"first_name": "Ada", "last_name": "Lovelace"}
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["first_name"], "Ada")
        self.assertEqual(body["tenant_id"], str(self._tenant_id))
        mock_create.assert_called_once()
        call_data = mock_create.call_args.args[0]
        self.assertEqual(call_data["tenant_id"], self._tenant_id)
        self.assertEqual(call_data["created_by"], self._user_id)

    async def test_create_contact_blank_first_name_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post("/api/v1/contacts", json={"first_name": "   "})
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_contact_email_too_long_returns_422(self):
        long_email = "a" * 250 + "@example.com"
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts", json={"first_name": "Ada", "email": long_email}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_contact_invalid_status_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts", json={"first_name": "Ada", "status": "bogus"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_contact_without_auth_returns_401(self):
        resp = await self.client.post("/api/v1/contacts", json={"first_name": "Ada"})
        self.assertEqual(resp.status_code, 401)

    async def test_create_contact_explicit_null_non_nullable_returns_422(self):
        # An explicit null on a NOT NULL column must 422, not reach the DB / 500.
        app = self._override_current_user()
        try:
            for field in ("status", "tags", "custom_fields"):
                resp = await self.client.post(
                    "/api/v1/contacts", json={"first_name": "Ada", field: None}
                )
                self.assertEqual(resp.status_code, 422, f"{field}=null should 422")
        finally:
            self._clear_override(app)

    # ── get ───────────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    async def test_get_contact_success(self, mock_get):
        mock_get.return_value = _fake_contact(self._contact_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.get(f"/api/v1/contacts/{self._contact_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], str(self._contact_id))
        mock_get.assert_called_once_with(self._tenant_id, self._contact_id)

    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    async def test_get_contact_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.get(f"/api/v1/contacts/{uuid.uuid4()}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "CONTACT_NOT_FOUND")

    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    async def test_get_contact_cross_tenant_returns_404_not_403(self, mock_get):
        # The repository always filters by tenant_id, so a contact belonging to
        # another tenant simply looks like "not found" to this caller.
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            other_tenant_contact_id = uuid.uuid4()
            resp = await self.client.get(f"/api/v1/contacts/{other_tenant_contact_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
        mock_get.assert_called_once_with(self._tenant_id, other_tenant_contact_id)

    # ── list ──────────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.list", new_callable=AsyncMock)
    async def test_list_contacts_success(self, mock_list):
        contact = _fake_contact(self._contact_id, self._tenant_id)
        mock_list.return_value = ([contact], 1)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["page_size"], 20)
        self.assertEqual(len(body["items"]), 1)

    @patch("app.modules.contacts.repository.ContactRepository.list", new_callable=AsyncMock)
    async def test_list_contacts_page_size_is_capped(self, mock_list):
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts?page_size=1000")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["page_size"], 100)
        mock_list.assert_called_once_with(self._tenant_id, 100, 0)

    # ── update ────────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_contact_success(self, mock_get, mock_update):
        existing = _fake_contact(self._contact_id, self._tenant_id)
        mock_get.return_value = existing
        mock_update.return_value = _fake_contact(
            self._contact_id, self._tenant_id, job_title="Engineer"
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}", json={"job_title": "Engineer"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["job_title"], "Engineer")
        update_data = mock_update.call_args.args[1]
        self.assertEqual(update_data["job_title"], "Engineer")
        self.assertEqual(update_data["updated_by"], self._user_id)
        self.assertNotIn("first_name", update_data)

    async def test_update_contact_explicit_null_first_name_returns_422(self):
        # first_name is NOT NULL — an explicit null on update must 422, not 500.
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}", json={"first_name": None}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_contact_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{uuid.uuid4()}", json={"job_title": "Engineer"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)

    # ── delete ────────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.delete", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    async def test_delete_contact_success(self, mock_get, mock_delete):
        mock_get.return_value = _fake_contact(self._contact_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.delete(f"/api/v1/contacts/{self._contact_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        mock_delete.assert_called_once()

    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    async def test_delete_contact_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.delete(f"/api/v1/contacts/{uuid.uuid4()}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
