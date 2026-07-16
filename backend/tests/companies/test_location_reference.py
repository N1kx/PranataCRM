import uuid
from unittest.mock import AsyncMock, patch

from app.modules.geo.exceptions import InvalidCountryReference, InvalidStateReference
from tests.companies.base import CompaniesTestCase
from tests.companies.test_companies import _fake_company


class LocationReferenceTests(CompaniesTestCase):
    """country/state/city on a company are validated via GeoContractProtocol
    (issue #26) — not just format-checked. This overrides the base class's
    default no-op geo patch to exercise the real validation call/propagation.
    """

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        # Stop the base class's default no-op geo patch for these tests —
        # each test below installs its own, more specific mock.
        self._geo_patcher.stop()
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

    @patch("app.modules.companies.repository.CompanyRepository.create", new_callable=AsyncMock)
    @patch("app.modules.geo.use_case.GeoUseCase.validate_location", new_callable=AsyncMock)
    async def test_create_company_calls_geo_validation_with_parsed_uuids(
        self, mock_validate, mock_create
    ) -> None:
        state_id = uuid.uuid4()
        city_id = uuid.uuid4()
        mock_create.return_value = _fake_company(self._company_id, self._tenant_id, country="ID")
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={
                    "name": "Acme", "phone": "0812", "country": "id",
                    "state": str(state_id), "city": str(city_id),
                },
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_validate.assert_awaited_once_with("ID", state_id, city_id)

    @patch("app.modules.companies.repository.CompanyRepository.create", new_callable=AsyncMock)
    @patch("app.modules.geo.use_case.GeoUseCase.validate_location", new_callable=AsyncMock)
    async def test_create_company_unknown_country_returns_422(
        self, mock_validate, mock_create
    ) -> None:
        mock_validate.side_effect = InvalidCountryReference()
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme", "phone": "0812", "country": "ZZ"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_COUNTRY_REFERENCE")
        mock_create.assert_not_called()

    async def test_create_company_country_not_2_letters_returns_422(self) -> None:
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme", "phone": "0812", "country": "Indonesia"},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    async def test_create_company_malformed_state_uuid_returns_422(self) -> None:
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/companies",
                json={"name": "Acme", "phone": "0812", "country": "ID", "state": "not-a-uuid"},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.companies.repository.CompanyRepository.update", new_callable=AsyncMock)
    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.geo.use_case.GeoUseCase.validate_location", new_callable=AsyncMock)
    async def test_update_state_only_merges_existing_country_before_validating(
        self, mock_validate, mock_get, mock_update
    ) -> None:
        # PATCH sends only `state` — the effective country used for cascade
        # validation must come from the already-stored company, not be
        # treated as missing (see CompanyUseCase.update_company).
        state_id = uuid.uuid4()
        existing = _fake_company(self._company_id, self._tenant_id, country="ID")
        mock_get.return_value = existing
        mock_update.return_value = _fake_company(
            self._company_id, self._tenant_id, country="ID", state=str(state_id)
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}",
                json={"state": str(state_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_validate.assert_awaited_once_with("ID", state_id, None)

    @patch("app.modules.companies.repository.CompanyRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.geo.use_case.GeoUseCase.validate_location", new_callable=AsyncMock)
    async def test_update_state_without_existing_country_returns_422(
        self, mock_validate, mock_get
    ) -> None:
        state_id = uuid.uuid4()
        existing = _fake_company(self._company_id, self._tenant_id, country=None)
        mock_get.return_value = existing
        mock_validate.side_effect = InvalidStateReference()
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/companies/{self._company_id}",
                json={"state": str(state_id)},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        mock_validate.assert_awaited_once_with(None, state_id, None)
