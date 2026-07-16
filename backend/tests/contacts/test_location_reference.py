import uuid
from unittest.mock import AsyncMock, patch

from app.modules.geo.exceptions import InvalidCountryReference
from tests.contacts.base import ContactsTestCase
from tests.contacts.test_contacts import _fake_contact


class LocationReferenceTests(ContactsTestCase):
    """country/state/city on a contact are validated via GeoContractProtocol
    (issue #26). Overrides the base class's default no-op geo patch."""

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._geo_patcher.stop()
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

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.geo.use_case.GeoUseCase.validate_location", new_callable=AsyncMock)
    async def test_create_contact_calls_geo_validation(self, mock_validate, mock_create) -> None:
        mock_create.return_value = _fake_contact(self._contact_id, self._tenant_id, country="ID")
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts", json={"first_name": "Jane", "country": "id"}
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_validate.assert_awaited_once_with("ID", None, None)

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.geo.use_case.GeoUseCase.validate_location", new_callable=AsyncMock)
    async def test_create_contact_unknown_country_returns_422(
        self, mock_validate, mock_create
    ) -> None:
        mock_validate.side_effect = InvalidCountryReference()
        app = self._override_current_user()
        try:
            resp = await self.client.post(
                "/api/v1/contacts", json={"first_name": "Jane", "country": "ZZ"}
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_COUNTRY_REFERENCE")
        mock_create.assert_not_called()

    @patch("app.modules.contacts.repository.ContactRepository.create", new_callable=AsyncMock)
    @patch("app.modules.geo.use_case.GeoUseCase.validate_location", new_callable=AsyncMock)
    async def test_create_contact_without_location_skips_geo_call_args_are_none(
        self, mock_validate, mock_create
    ) -> None:
        mock_create.return_value = _fake_contact(self._contact_id, self._tenant_id)
        app = self._override_current_user()
        try:
            resp = await self.client.post("/api/v1/contacts", json={"first_name": "Jane"})
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 201)
        mock_validate.assert_awaited_once_with(None, None, None)

    @patch("app.modules.contacts.repository.ContactRepository.update", new_callable=AsyncMock)
    @patch("app.modules.contacts.repository.ContactRepository.get_by_id", new_callable=AsyncMock)
    @patch("app.modules.geo.use_case.GeoUseCase.validate_location", new_callable=AsyncMock)
    async def test_update_country_with_legacy_free_text_state_does_not_500(
        self, mock_validate, mock_get, mock_update
    ) -> None:
        # Pre-#26 rows can still have free-text state/city (the backfill
        # script never attempts state; city stays free text when no match is
        # found). PATCHing country alone merges in that legacy value as
        # "current.state" — it must not crash trying to parse it as a UUID.
        existing = _fake_contact(
            self._contact_id, self._tenant_id, country="ID", state="Jakarta", city="Jakarta",
        )
        mock_get.return_value = existing
        mock_update.return_value = _fake_contact(
            self._contact_id, self._tenant_id, country="US", state="Jakarta", city="Jakarta",
        )
        app = self._override_current_user()
        try:
            resp = await self.client.patch(
                f"/api/v1/contacts/{self._contact_id}",
                json={"country": "US"},
            )
        finally:
            self._clear_override(app)

        self.assertEqual(resp.status_code, 200)
        mock_validate.assert_awaited_once_with("US", None, None)
