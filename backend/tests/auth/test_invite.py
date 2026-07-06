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

    @patch("app.modules.auth.repository.AuthRepository.get_user_by_email", new_callable=AsyncMock)
    @patch("app.modules.auth.service.send_invite_email", new_callable=AsyncMock)
    @patch("app.modules.auth.service.AuthService._get_tenant_by_id", new_callable=AsyncMock)
    async def test_owner_sends_invite(self, mock_get_tenant, mock_send_email, mock_get_email):
        from app.main import app
        from app.modules.auth.router import CurrentUser, get_current_user
        mock_get_tenant.return_value = _fake_tenant(self._tenant_id)
        mock_get_email.return_value = None

        async def _override():
            return CurrentUser(user_id=self._owner_id, tenant_id=self._tenant_id, suite_role="tenant_owner")

        app.dependency_overrides[get_current_user] = _override
        try:
            resp = await self.client.post("/api/v1/users/invite", json={
                "email": "invitee@nxcorp.co",
                "full_name": "Invited User",
                "role_id": str(uuid.uuid4()),
            }, headers={"X-Tenant-Slug": "nxcorp"})
        finally:
            app.dependency_overrides.pop(get_current_user, None)

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

    async def test_accept_invite_token_missing_claims(self):
        # A signature-valid invite token that lacks the required claims must be
        # rejected as an invalid invite (400), not crash with a 500.
        import jwt as _jwt
        from datetime import datetime, timedelta, timezone
        from app.config import get_settings
        settings = get_settings()
        now = datetime.now(timezone.utc)
        token = _jwt.encode(
            {"purpose": "invite", "iat": now, "exp": now + timedelta(days=1)},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        resp = await self.client.post("/api/v1/auth/accept-invite", json={
            "token": token,
            "full_name": "Bug Demo",
            "password": "secret123",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_INVITE_INVALID")
