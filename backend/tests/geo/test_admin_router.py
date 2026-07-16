from unittest.mock import AsyncMock, patch

from tests.geo.base import GeoTestCase


class AdminGeoRouterTests(GeoTestCase):
    """/admin/geo/* — gated to tenant_owner (interim platform-admin proxy,
    see the TODO in admin_router.py); everyone else gets 403."""

    @patch("app.modules.geo.repository.GeoRepository.create_state", new_callable=AsyncMock)
    @patch("app.modules.geo.repository.GeoRepository.list_active_states", new_callable=AsyncMock)
    async def test_member_cannot_create_state(self, mock_list, mock_create) -> None:
        app = self._override_current_user(suite_role="member")
        try:
            resp = await self.client.post(
                "/api/v1/admin/geo/states", json={"country_code": "ID", "name": "Jawa Barat"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 403)
        mock_create.assert_not_called()

    @patch("app.modules.geo.use_case.GeoUseCase.create_state", new_callable=AsyncMock)
    async def test_tenant_owner_can_create_state(self, mock_create) -> None:
        mock_create.return_value = {
            "id": "11111111-1111-1111-1111-111111111111",
            "country_code": "ID",
            "name": "Jawa Barat",
            "code": None,
            "is_active": True,
        }
        app = self._override_current_user(suite_role="tenant_owner")
        try:
            resp = await self.client.post(
                "/api/v1/admin/geo/states", json={"country_code": "ID", "name": "Jawa Barat"}
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 201)
        mock_create.assert_awaited_once()

    async def test_create_state_invalid_country_code_format_returns_422(self) -> None:
        app = self._override_current_user(suite_role="tenant_owner")
        try:
            resp = await self.client.post(
                "/api/v1/admin/geo/states",
                json={"country_code": "Indonesia", "name": "Jawa Barat"},
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 422)

    @patch("app.modules.geo.use_case.GeoUseCase.delete_state", new_callable=AsyncMock)
    async def test_member_cannot_delete_state(self, mock_delete) -> None:
        app = self._override_current_user(suite_role="member")
        try:
            resp = await self.client.delete(
                "/api/v1/admin/geo/states/11111111-1111-1111-1111-111111111111"
            )
        finally:
            self._clear_override(app)
        self.assertEqual(resp.status_code, 403)
        mock_delete.assert_not_called()
