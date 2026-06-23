import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.auth.base import AuthTestCase


def _fake_tenant(tenant_id: uuid.UUID, slug: str = "nxcorp") -> SimpleNamespace:
    return SimpleNamespace(id=tenant_id, slug=slug)


class InviteTests(AuthTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._tenant_id = uuid.uuid4()
        self._owner_id = uuid.uuid4()

    @patch("app.modules.auth.router.get_current_user")
    @patch("app.modules.auth.repository.AuthRepository.get_user_by_email", new_callable=AsyncMock)
    @patch("app.modules.auth.service.send_invite_email", new_callable=AsyncMock)
    @patch("app.modules.auth.service.AuthService._get_tenant_by_id", new_callable=AsyncMock)
    async def test_owner_sends_invite(
        self, mock_get_tenant, mock_send_email, mock_get_email, mock_current_user
    ):
        from app.modules.auth.router import CurrentUser
        mock_get_tenant.return_value = _fake_tenant(self._tenant_id)
        mock_get_email.return_value = None
        mock_current_user.return_value = CurrentUser(
            user_id=self._owner_id,
            tenant_id=self._tenant_id,
            suite_role="tenant_owner",
        )

        resp = await self.client.post("/api/v1/users/invite", json={
            "email": "invitee@nxcorp.co",
            "full_name": "Invited User",
            "role_id": str(uuid.uuid4()),
        }, headers={"X-Tenant-Slug": "nxcorp"})
        self.assertIn(resp.status_code, (200, 201))
        mock_send_email.assert_called_once()

    async def test_accept_invite_invalid_token(self):
        resp = await self.client.post("/api/v1/auth/accept-invite", json={
            "token": "invalid-token",
            "full_name": "X",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_INVITE_INVALID")
