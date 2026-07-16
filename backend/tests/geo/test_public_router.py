from unittest.mock import AsyncMock, patch

from tests.geo.base import GeoTestCase


class PublicLookupRouterTests(GeoTestCase):
    """GET /geo/countries|states|cities — query-param validation and the
    standard {"error": {code, ...}} envelope (not FastAPI's default shape)."""

    @patch("app.modules.geo.use_case.GeoUseCase.list_countries", new_callable=AsyncMock)
    async def test_list_countries_returns_data(self, mock_list) -> None:
        mock_list.return_value = [
            {"code": "ID", "name_en": "Indonesia", "name_id": None, "is_active": True}
        ]
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/geo/countries")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["code"], "ID")

    async def test_list_states_missing_country_returns_422_with_standard_envelope(self) -> None:
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/geo/states")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "VALIDATION_ERROR")

    @patch("app.modules.geo.use_case.GeoUseCase.list_states", new_callable=AsyncMock)
    async def test_list_states_passes_country_through(self, mock_list) -> None:
        mock_list.return_value = []
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/geo/states?country=ID")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 200)
        mock_list.assert_awaited_once_with("ID")

    async def test_list_cities_missing_state_returns_422(self) -> None:
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/geo/cities")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "VALIDATION_ERROR")

    async def test_list_cities_malformed_state_uuid_returns_422(self) -> None:
        app = self._override_current_user()
        try:
            resp = await self.client.get("/api/v1/geo/cities?state=not-a-uuid")
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "VALIDATION_ERROR")
