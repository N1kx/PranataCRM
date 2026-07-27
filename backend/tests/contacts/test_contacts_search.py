import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.contacts.base import ContactsTestCase


def _fake_contact(
    contact_id: uuid.UUID,
    tenant_id: uuid.UUID,
    first_name: str = "Budi",
    last_name: str | None = "Santoso",
    email: str | None = None,
    company_id: uuid.UUID | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=contact_id,
        tenant_id=tenant_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        company_id=company_id,
    )


class ContactsSearchTests(ContactsTestCase):
    """GET /contacts/search + /contacts/lookup — the autocomplete/batched-label
    endpoints backing AppContactSelect (issue #38), mirroring companies."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._caller_id = uuid.uuid4()

    def _override_current_user(self) -> None:
        from app.main import app
        from app.modules.auth.dependencies import CurrentUser, get_current_user

        async def _override():
            return CurrentUser(
                user_id=self._caller_id, tenant_id=self._tenant_id, suite_role="member",
            )

        app.dependency_overrides[get_current_user] = _override

    def _clear_override(self) -> None:
        from app.main import app
        from app.modules.auth.dependencies import get_current_user
        app.dependency_overrides.pop(get_current_user, None)

    # ── search ────────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.search", new_callable=AsyncMock)
    async def test_search_returns_joined_display_name(self, mock_search):
        mock_search.return_value = [
            _fake_contact(uuid.uuid4(), self._tenant_id, "Budi", "Santoso", "budi@acme.io"),
        ]
        self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts/search", params={"q": "budi"})
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Budi Santoso")
        self.assertEqual(data[0]["email"], "budi@acme.io")
        self.assertEqual(mock_search.call_args.args[0], self._tenant_id)

    @patch("app.modules.contacts.repository.ContactRepository.search", new_callable=AsyncMock)
    async def test_search_name_without_last_name_is_not_padded(self, mock_search):
        # A missing last_name must not leave a trailing space in the label.
        mock_search.return_value = [
            _fake_contact(uuid.uuid4(), self._tenant_id, "Budi", None),
        ]
        self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts/search")
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["name"], "Budi")

    @patch("app.modules.contacts.repository.ContactRepository.search", new_callable=AsyncMock)
    async def test_search_scopes_to_company_when_given(self, mock_search):
        mock_search.return_value = []
        company_id = uuid.uuid4()
        self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/contacts/search", params={"company_id": str(company_id)},
            )
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_search.call_args.args[3], company_id)

    async def test_search_invalid_company_id_returns_422(self):
        self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/contacts/search", params={"company_id": "not-a-uuid"},
            )
        finally:
            self._clear_override()
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "VALIDATION_ERROR")

    async def test_search_limit_out_of_range_returns_422(self):
        self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts/search", params={"limit": 0})
        finally:
            self._clear_override()
        self.assertEqual(resp.status_code, 422)

    # ── lookup ────────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.get_by_ids", new_callable=AsyncMock)
    async def test_lookup_returns_summaries_for_ids(self, mock_get_by_ids):
        id_a, id_b = uuid.uuid4(), uuid.uuid4()
        mock_get_by_ids.return_value = [
            _fake_contact(id_a, self._tenant_id, "Budi", "Santoso"),
            _fake_contact(id_b, self._tenant_id, "Siti", "Rahayu"),
        ]
        self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/contacts/lookup", params={"ids": f"{id_a},{id_b}"},
            )
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual([c["name"] for c in data], ["Budi Santoso", "Siti Rahayu"])
        self.assertEqual(mock_get_by_ids.call_args.args[1], [id_a, id_b])

    @patch("app.modules.contacts.repository.ContactRepository.get_by_ids", new_callable=AsyncMock)
    async def test_lookup_skips_malformed_ids(self, mock_get_by_ids):
        # A malformed id is dropped rather than 422-ing the whole batch, so one
        # bad reference can't blank out every label on a list page.
        good = uuid.uuid4()
        mock_get_by_ids.return_value = []
        self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/contacts/lookup", params={"ids": f"{good},not-a-uuid,"},
            )
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_get_by_ids.call_args.args[1], [good])

    @patch("app.modules.contacts.repository.ContactRepository.get_by_ids", new_callable=AsyncMock)
    async def test_lookup_empty_ids_returns_empty_list(self, mock_get_by_ids):
        mock_get_by_ids.return_value = []
        self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts/lookup")
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    # ── routing ───────────────────────────────────────────────────────────────

    @patch("app.modules.contacts.repository.ContactRepository.search", new_callable=AsyncMock)
    async def test_search_path_is_not_swallowed_by_contact_id_route(self, mock_search):
        # /contacts/search must match the literal route, not GET /contacts/{id}
        # (which would 422 on "search" not being a UUID).
        mock_search.return_value = []
        self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/contacts/search")
        finally:
            self._clear_override()
        self.assertEqual(resp.status_code, 200)
        mock_search.assert_called_once()
