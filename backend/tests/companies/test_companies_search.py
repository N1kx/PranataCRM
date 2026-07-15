import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from tests.common import make_mock_session
from tests.companies.base import CompaniesTestCase


def _fake_company(
    company_id: uuid.UUID,
    tenant_id: uuid.UUID,
    name: str = "Acme Corp",
    domain: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(id=company_id, tenant_id=tenant_id, name=name, domain=domain)


class CompaniesSearchTests(CompaniesTestCase):

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

    @patch("app.modules.companies.repository.CompanyRepository.search", new_callable=AsyncMock)
    async def test_search_matches_by_name(self, mock_search):
        mock_search.return_value = [
            _fake_company(uuid.uuid4(), self._tenant_id, name="Acme Corp", domain="acme.io"),
        ]
        self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies/search", params={"q": "acme"})
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Acme Corp")
        self.assertEqual(data[0]["domain"], "acme.io")
        called_tenant_id = mock_search.call_args.args[0]
        self.assertEqual(called_tenant_id, self._tenant_id)

    @patch("app.modules.companies.repository.CompanyRepository.search", new_callable=AsyncMock)
    async def test_search_matches_by_domain(self, mock_search):
        mock_search.return_value = [
            _fake_company(uuid.uuid4(), self._tenant_id, name="Beta Inc", domain="beta.co"),
        ]
        self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies/search", params={"q": "beta.co"})
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["domain"], "beta.co")

    @patch("app.modules.companies.repository.CompanyRepository.search", new_callable=AsyncMock)
    async def test_search_empty_query_returns_first_n(self, mock_search):
        mock_search.return_value = [
            _fake_company(uuid.uuid4(), self._tenant_id, name="Acme"),
            _fake_company(uuid.uuid4(), self._tenant_id, name="Beta"),
        ]
        self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/companies/search")
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)
        mock_search.assert_called_once_with(self._tenant_id, "", 20)

    @patch("app.modules.companies.repository.CompanyRepository.search", new_callable=AsyncMock)
    async def test_search_scopes_to_caller_tenant(self, mock_search):
        mock_search.return_value = []
        self._override_current_user()
        try:
            await self.client.get("/api/v1/companies/search", params={"q": "x"})
        finally:
            self._clear_override()

        called_tenant_id = mock_search.call_args.args[0]
        self.assertEqual(called_tenant_id, self._tenant_id)

    async def test_search_without_cookie_returns_401(self):
        resp = await self.client.get("/api/v1/companies/search", params={"q": "x"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_NOT_AUTHENTICATED")

    @patch("app.modules.companies.repository.CompanyRepository.search", new_callable=AsyncMock)
    async def test_search_negative_limit_rejected(self, mock_search):
        # A negative limit would compile to SQL "LIMIT -1", which Postgres
        # rejects with a 500. It must be rejected at the edge as a 422 and
        # never reach the repository.
        mock_search.return_value = []
        self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/companies/search", params={"q": "x", "limit": -1},
            )
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 422)
        mock_search.assert_not_called()

    @patch("app.modules.companies.repository.CompanyRepository.search", new_callable=AsyncMock)
    async def test_search_limit_above_max_rejected(self, mock_search):
        mock_search.return_value = []
        self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/companies/search", params={"q": "x", "limit": 999},
            )
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 422)
        mock_search.assert_not_called()

    async def test_search_escapes_like_wildcards(self):
        # A term containing LIKE wildcards must be escaped so it matches those
        # characters literally instead of acting as a pattern.
        from app.modules.companies.repository import CompanyRepository

        session = make_mock_session()
        result_obj = MagicMock()
        result_obj.scalars.return_value.all.return_value = []
        session.execute.return_value = result_obj

        repo = CompanyRepository(session)
        await repo.search(uuid.uuid4(), "50%_x", 20)

        stmt = session.execute.call_args.args[0]
        params = stmt.compile().params
        self.assertTrue(
            any(isinstance(v, str) and v == "%50\\%\\_x%" for v in params.values()),
            f"expected escaped LIKE pattern in {params}",
        )

    @patch("app.modules.companies.repository.CompanyRepository.get_by_ids", new_callable=AsyncMock)
    async def test_lookup_returns_matching_summaries(self, mock_lookup):
        id1, id2 = uuid.uuid4(), uuid.uuid4()
        mock_lookup.return_value = [
            _fake_company(id1, self._tenant_id, name="Acme"),
            _fake_company(id2, self._tenant_id, name="Beta"),
        ]
        self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/companies/lookup", params={"ids": f"{id1},{id2}"},
            )
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual({c["name"] for c in data}, {"Acme", "Beta"})
        called_tenant_id, called_ids = mock_lookup.call_args.args
        self.assertEqual(called_tenant_id, self._tenant_id)
        self.assertEqual(set(called_ids), {id1, id2})

    @patch("app.modules.companies.repository.CompanyRepository.get_by_ids", new_callable=AsyncMock)
    async def test_lookup_skips_invalid_ids_instead_of_500(self, mock_lookup):
        mock_lookup.return_value = []
        self._override_current_user()
        try:
            resp = await self.client.get(
                "/api/v1/companies/lookup", params={"ids": "not-a-uuid,,  "},
            )
        finally:
            self._clear_override()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])
        mock_lookup.assert_called_once_with(self._tenant_id, [])

    @patch("app.modules.companies.repository.CompanyRepository.get_by_ids", new_callable=AsyncMock)
    async def test_lookup_scopes_to_caller_tenant(self, mock_lookup):
        mock_lookup.return_value = []
        cid = uuid.uuid4()
        self._override_current_user()
        try:
            await self.client.get("/api/v1/companies/lookup", params={"ids": str(cid)})
        finally:
            self._clear_override()

        called_tenant_id = mock_lookup.call_args.args[0]
        self.assertEqual(called_tenant_id, self._tenant_id)

    async def test_lookup_without_cookie_returns_401(self):
        resp = await self.client.get("/api/v1/companies/lookup", params={"ids": ""})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_NOT_AUTHENTICATED")
