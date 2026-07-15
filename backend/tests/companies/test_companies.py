import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.companies.base import CompaniesTestCase


def _fake_company(
    company_id: uuid.UUID,
    tenant_id: uuid.UUID,
    name: str = "Acme Corp",
    **overrides,
) -> SimpleNamespace:
    defaults = dict(
        id=company_id,
        tenant_id=tenant_id,
        owner_id=None,
        name=name,
        legal_name=None,
        domain=None,
        website=None,
        email=None,
        phone=None,
        industry=None,
        size=None,
        employee_count=None,
        company_type="prospect",
        status="active",
        arr=None,
        annual_revenue=None,
        source=None,
        address_line1=None,
        address_line2=None,
        city=None,
        state=None,
        postal_code=None,
        country=None,
        timezone=None,
        linkedin_url=None,
        twitter_handle=None,
        logo_url=None,
        description=None,
        tags=[],
        custom_fields={},
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class CompaniesTests(CompaniesTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._user_id = uuid.uuid4()
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

    # name/phone/country are required on create (business rule, not a DB
    # constraint) - every other create test includes them so a 422 there
    # is unambiguously about the field under test, not a missing required field.
    _REQUIRED_CREATE_FIELDS = {"phone": "+62 812-0000-0000", "country": "Indonesia"}

    @patch("app.modules.companies.repository.CompanyRepository.create", new_callable=AsyncMock)
    async def test_create_company_success(self, mock_create):
        mock_create.return_value = _fake_company(self._company_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme Corp", **self._REQUIRED_CREATE_FIELDS},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["name"], "Acme Corp")
        self.assertEqual(body["tenant_id"], str(self._tenant_id))
        mock_create.assert_called_once()
        call_data = mock_create.call_args.args[0]
        self.assertEqual(call_data["tenant_id"], self._tenant_id)
        self.assertEqual(call_data["created_by"], self._user_id)

    async def test_create_company_blank_name_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "   ", **self._REQUIRED_CREATE_FIELDS},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_missing_phone_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies", json={"name": "Acme", "country": "Indonesia"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_blank_phone_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme", "phone": "   ", "country": "Indonesia"},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_null_phone_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme", "phone": None, "country": "Indonesia"},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_missing_country_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies", json={"name": "Acme", "phone": "0812"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_blank_country_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme", "phone": "0812", "country": "  "},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_null_country_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme", "phone": "0812", "country": None},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_invalid_company_type_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={
                    "name": "Acme", "company_type": "bogus",
                    **self._REQUIRED_CREATE_FIELDS,
                },
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_invalid_status_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={
                    "name": "Acme", "status": "bogus", **self._REQUIRED_CREATE_FIELDS,
                },
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_invalid_size_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme", "size": "bogus", **self._REQUIRED_CREATE_FIELDS},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_invalid_owner_id_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={
                    "name": "Acme", "owner_id": "not-a-uuid",
                    **self._REQUIRED_CREATE_FIELDS,
                },
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_invalid_email_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={
                    "name": "Acme", "email": "not-an-email",
                    **self._REQUIRED_CREATE_FIELDS,
                },
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_without_auth_returns_401(self):
        resp = await self.client.post(
            "/api/v1/companies", json={"name": "Acme", **self._REQUIRED_CREATE_FIELDS}
        )
        self.assertEqual(resp.status_code, 401)

    async def test_create_company_explicit_null_non_nullable_returns_422(self):
        # An explicit null on a NOT NULL column must 422, not reach the DB / 500.
        app = self._override_current_user()
        try:
            for field in ("company_type", "status", "tags", "custom_fields"):
                resp = await self.client.post(
                    "/api/v1/companies",
                    json={
                        "name": "Acme", field: None, **self._REQUIRED_CREATE_FIELDS,
                    },
                )
                self.assertEqual(resp.status_code, 422, f"{field}=null should 422")
        finally:
            self._clear_override(app)

    # ── get ───────────────────────────────────────────────────────────────────

    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_get_company_success(self, mock_get):
        mock_get.return_value = _fake_company(self._company_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.get(f"/api/v1/companies/{self._company_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], str(self._company_id))
        mock_get.assert_called_once_with(self._tenant_id, self._company_id)

    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_get_company_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.get(f"/api/v1/companies/{uuid.uuid4()}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "COMPANY_NOT_FOUND")

    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_get_company_cross_tenant_returns_404_not_403(self, mock_get):
        # The repository always filters by tenant_id, so a company belonging to
        # another tenant simply looks like "not found" to this caller.
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            other_tenant_company_id = uuid.uuid4()
            resp = await self.client.get(f"/api/v1/companies/{other_tenant_company_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
        mock_get.assert_called_once_with(self._tenant_id, other_tenant_company_id)

    # ── list / pagination ────────────────────────────────────────────────────

    @patch("app.modules.companies.repository.CompanyRepository.list", new_callable=AsyncMock)
    async def test_list_companies_success(self, mock_list):
        company = _fake_company(self._company_id, self._tenant_id)
        mock_list.return_value = ([company], 1)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["page_size"], 20)
        self.assertEqual(len(body["items"]), 1)

    @patch("app.modules.companies.repository.CompanyRepository.list", new_callable=AsyncMock)
    async def test_list_companies_page_size_is_capped(self, mock_list):
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?page_size=1000")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["page_size"], 100)
        call_kwargs = mock_list.call_args.kwargs
        mock_list.assert_called_once()
        self.assertEqual(mock_list.call_args.args, (self._tenant_id, 100, 0))
        self.assertEqual(call_kwargs["sort"], "created_at")
        self.assertEqual(call_kwargs["order"], "desc")

    @patch("app.modules.companies.repository.CompanyRepository.list", new_callable=AsyncMock)
    async def test_list_companies_defaults_match_plain_pagination(self, mock_list):
        # No filter/sort/search params -> behavior identical to plain pagination.
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            await self.client.get("/api/v1/companies")
        finally:
            self._clear_override(app)
        call_kwargs = mock_list.call_args.kwargs
        self.assertIsNone(call_kwargs["status"])
        self.assertIsNone(call_kwargs["company_type"])
        self.assertIsNone(call_kwargs["size"])
        self.assertIsNone(call_kwargs["industry"])
        self.assertIsNone(call_kwargs["owner_id"])
        self.assertIsNone(call_kwargs["q"])
        self.assertEqual(call_kwargs["sort"], "created_at")
        self.assertEqual(call_kwargs["order"], "desc")

    # ── filter/sort/search ───────────────────────────────────────────────────

    @patch("app.modules.companies.repository.CompanyRepository.list", new_callable=AsyncMock)
    async def test_list_companies_filters_by_status(self, mock_list):
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?status=active")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_list.call_args.kwargs["status"], "active")

    async def test_list_companies_invalid_status_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?status=bogus")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("status must be one of", resp.json()["error"]["message"])

    async def test_list_companies_invalid_company_type_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?company_type=bogus")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_companies_invalid_size_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?size=bogus")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_companies_invalid_owner_id_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?owner_id=not-a-uuid")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.companies.repository.CompanyRepository.list", new_callable=AsyncMock)
    async def test_list_companies_owner_id_parsed_as_uuid(self, mock_list):
        mock_list.return_value = ([], 0)
        owner_id = uuid.uuid4()
        app = self._override_current_user()
        try:
            await self.client.get(f"/api/v1/companies?owner_id={owner_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(mock_list.call_args.kwargs["owner_id"], owner_id)

    @patch("app.modules.companies.repository.CompanyRepository.list", new_callable=AsyncMock)
    async def test_list_companies_search_q_passed_through(self, mock_list):
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?q=acme")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_list.call_args.kwargs["q"], "acme")

    async def test_list_companies_q_too_long_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get(f"/api/v1/companies?q={'a' * 101}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.companies.repository.CompanyRepository.list", new_callable=AsyncMock)
    async def test_list_companies_sort_and_order(self, mock_list):
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?sort=name&order=asc")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_list.call_args.kwargs["sort"], "name")
        self.assertEqual(mock_list.call_args.kwargs["order"], "asc")

    async def test_list_companies_sort_outside_allowlist_returns_422(self):
        # "id" is a real column but not in the allowlist — must still 422, since
        # the allowlist (not "is it a real column") is the security boundary.
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?sort=id")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_list_companies_invalid_order_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies?sort=name&order=sideways")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.companies.repository.CompanyRepository.list", new_callable=AsyncMock)
    async def test_list_companies_combines_filters(self, mock_list):
        # All params are optional and combinable (AND semantics).
        mock_list.return_value = ([], 0)
        app = self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/companies"
                "?status=active&company_type=customer&size=11-50"
                "&industry=Tech&q=acme&sort=employee_count&order=asc"
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        kwargs = mock_list.call_args.kwargs
        self.assertEqual(kwargs["status"], "active")
        self.assertEqual(kwargs["company_type"], "customer")
        self.assertEqual(kwargs["size"], "11-50")
        self.assertEqual(kwargs["industry"], "Tech")
        self.assertEqual(kwargs["q"], "acme")
        self.assertEqual(kwargs["sort"], "employee_count")
        self.assertEqual(kwargs["order"], "asc")

    async def test_list_companies_without_auth_returns_401(self):
        resp = await self.client.get("/api/v1/companies")
        self.assertEqual(resp.status_code, 401)

    # ── update ────────────────────────────────────────────────────────────────

    @patch("app.modules.companies.repository.CompanyRepository.update", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_company_success(self, mock_get, mock_update):
        existing = _fake_company(self._company_id, self._tenant_id)
        mock_get.return_value = existing
        mock_update.return_value = _fake_company(
            self._company_id, self._tenant_id, industry="Software"
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}", json={"industry": "Software"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["industry"], "Software")
        update_data = mock_update.call_args.args[1]
        self.assertEqual(update_data["industry"], "Software")
        self.assertEqual(update_data["updated_by"], self._user_id)
        self.assertNotIn("name", update_data)

    async def test_update_company_explicit_null_name_returns_422(self):
        # name is NOT NULL — an explicit null on update must 422, not 500.
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}", json={"name": None}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_update_company_explicit_null_phone_returns_422(self):
        # phone is mandatory (business rule) — clearing it via PATCH must 422.
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}", json={"phone": None}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_update_company_blank_phone_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}", json={"phone": "   "}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_update_company_explicit_null_country_returns_422(self):
        # country is mandatory (business rule) — clearing it via PATCH must 422.
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}", json={"country": None}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_update_company_blank_country_returns_422(self):
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}", json={"country": "  "}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.companies.repository.CompanyRepository.update", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_company_phone_and_country_success(self, mock_get, mock_update):
        # Sending a real value (not clearing it) is a normal partial update.
        mock_get.return_value = _fake_company(self._company_id, self._tenant_id)
        mock_update.return_value = _fake_company(
            self._company_id, self._tenant_id, phone="0812", country="Indonesia"
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}",
                json={"phone": "0812", "country": "Indonesia"},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        update_data = mock_update.call_args.args[1]
        self.assertEqual(update_data["phone"], "0812")
        self.assertEqual(update_data["country"], "Indonesia")

    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_update_company_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{uuid.uuid4()}", json={"industry": "Software"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)

    # ── delete ────────────────────────────────────────────────────────────────

    @patch("app.modules.companies.repository.CompanyRepository.delete", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_delete_company_success(self, mock_get, mock_delete):
        mock_get.return_value = _fake_company(self._company_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.delete(f"/api/v1/companies/{self._company_id}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        mock_delete.assert_called_once()

    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    async def test_delete_company_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        app = self._override_current_user()
        try:
            resp = await self.client.delete(f"/api/v1/companies/{uuid.uuid4()}")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 404)
