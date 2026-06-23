import uuid
from unittest.mock import AsyncMock, patch

from tests.auth.base import AuthTestCase


class LogoutTests(AuthTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        from app.shared.jwt import create_access_token, create_refresh_token
        access = create_access_token(str(user_id), str(tenant_id))
        refresh, _ = create_refresh_token(str(user_id), str(tenant_id))
        self.client.cookies.set("access_token", access)
        self.client.cookies.set("refresh_token", refresh)

    @patch("app.modules.auth.repository.AuthRepository.revoke_refresh_token", new_callable=AsyncMock)
    async def test_logout_clears_cookies(self, mock_revoke):
        resp = await self.client.post(
            "/api/v1/auth/logout",
            headers={"X-Tenant-Slug": "nxcorp"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["message"], "Signed out successfully.")
        mock_revoke.assert_called_once()

    @patch("app.modules.auth.repository.AuthRepository.revoke_refresh_token", new_callable=AsyncMock)
    async def test_logout_without_session_is_idempotent(self, mock_revoke):
        self.client.cookies.clear()
        resp1 = await self.client.post(
            "/api/v1/auth/logout",
            headers={"X-Tenant-Slug": "nxcorp"},
        )
        resp2 = await self.client.post(
            "/api/v1/auth/logout",
            headers={"X-Tenant-Slug": "nxcorp"},
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
