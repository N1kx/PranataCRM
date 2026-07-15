import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from tests.common import make_mock_session
from tests.contacts.base import ContactsTestCase


class ContactsFiltersTests(ContactsTestCase):
    """GET /contacts filter, sort, and search query params (issue #22)."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()

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

    async def test_list_contacts_invalid_status_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts?status=bogus")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertIn("status must be one of", resp.json()["error"]["message"])

    async def test_list_contacts_invalid_lifecycle_stage_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts?lifecycle_stage=bogus")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_contacts_invalid_owner_id_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts?owner_id=not-a-uuid")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_contacts_invalid_company_id_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts?company_id=not-a-uuid")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_contacts_sort_outside_allowlist_returns_422(self):
        # "id" is a real column but not in the allowlist — must still 422, since
        # the allowlist (not "is it a real column") is the security boundary.
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts?sort=id")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_contacts_invalid_order_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts?sort=first_name&order=sideways")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_contacts_q_too_long_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get(f"/api/v1/contacts?q={'a' * 101}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_contacts_without_auth_returns_401(self):
        resp = await self.client.get("/api/v1/contacts?status=lead")
        self.assertEqual(resp.status_code, 401)

    @patch("app.modules.contacts.repository.ContactRepository.list", new_callable=AsyncMock)
    async def test_list_contacts_combines_filters(self, mock_list):
        # All params are optional and combinable (AND semantics).
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/contacts"
                "?status=lead&lifecycle_stage=mql&q=ada&sort=first_name&order=asc"
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        kwargs = mock_list.call_args.kwargs
        self.assertEqual(kwargs["status"], "lead")
        self.assertEqual(kwargs["lifecycle_stage"], "mql")
        self.assertEqual(kwargs["q"], "ada")
        self.assertEqual(kwargs["sort"], "first_name")
        self.assertEqual(kwargs["order"], "asc")

    @patch("app.modules.contacts.repository.ContactRepository.list", new_callable=AsyncMock)
    async def test_list_contacts_owner_id_parsed_as_uuid(self, mock_list):
        mock_list.return_value = ([], 0)
        owner_id = uuid.uuid4()
        app = self._override_current_user()
        try:
            await self.client.get(f"/api/v1/contacts?owner_id={owner_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(mock_list.call_args.kwargs["owner_id"], owner_id)

    @patch("app.modules.contacts.repository.ContactRepository.list", new_callable=AsyncMock)
    async def test_list_contacts_company_id_parsed_as_uuid(self, mock_list):
        mock_list.return_value = ([], 0)
        company_id = uuid.uuid4()
        app = self._override_current_user()
        try:
            await self.client.get(f"/api/v1/contacts?company_id={company_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(mock_list.call_args.kwargs["company_id"], company_id)

    @patch("app.modules.contacts.repository.ContactRepository.list", new_callable=AsyncMock)
    async def test_list_contacts_no_params_uses_defaults(self, mock_list):
        # No params -> behavior identical to today (newest-first, same shape).
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        kwargs = mock_list.call_args.kwargs
        self.assertIsNone(kwargs["status"])
        self.assertIsNone(kwargs["lifecycle_stage"])
        self.assertIsNone(kwargs["owner_id"])
        self.assertIsNone(kwargs["company_id"])
        self.assertIsNone(kwargs["q"])
        self.assertEqual(kwargs["sort"], "created_at")
        self.assertEqual(kwargs["order"], "desc")

    async def test_list_repository_escapes_like_wildcards(self):
        # A term containing LIKE wildcards must be escaped so it matches those
        # characters literally instead of acting as a pattern.
        from app.modules.contacts.repository import ContactRepository

        session = make_mock_session()
        result_obj = MagicMock()
        result_obj.scalars.return_value.all.return_value = []
        session.execute.return_value = result_obj

        repo = ContactRepository(session)
        await repo.list(uuid.uuid4(), 20, 0, q="50%_x")

        stmt = session.execute.call_args_list[0].args[0]
        params = stmt.compile().params
        self.assertTrue(
            any(isinstance(v, str) and v == "%50\\%\\_x%" for v in params.values()),
            f"expected escaped LIKE pattern in {params}",
        )
