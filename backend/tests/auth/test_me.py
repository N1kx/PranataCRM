import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.auth.base import AuthTestCase


def _fake_user(user_id: uuid.UUID, tenant_id: uuid.UUID) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        tenant_id=tenant_id,
        email="niko@nxcorp.co",
        full_name="Niko Winoko",
        suite_role="tenant_owner",
        is_active=True,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class MeTests(AuthTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._user_id = uuid.uuid4()
        self._tenant_id = uuid.uuid4()

    @patch("app.modules.auth.repository.AuthRepository.get_user_by_id", new_callable=AsyncMock)
    async def test_me_returns_user_profile(self, mock_get_user):
        from app.main import app
        from app.modules.auth.router import CurrentUser, get_current_user

        mock_get_user.return_value = _fake_user(self._user_id, self._tenant_id)

        async def _override():
            return CurrentUser(
                user_id=self._user_id,
                tenant_id=self._tenant_id,
                suite_role="tenant_owner",
            )

        app.dependency_overrides[get_current_user] = _override
        try:
            resp = await self.client.get("/api/v1/auth/me")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["email"], "niko@nxcorp.co")
        self.assertEqual(data["full_name"], "Niko Winoko")
        self.assertEqual(data["suite_role"], "tenant_owner")
        self.assertEqual(data["tenant_id"], str(self._tenant_id))
        self.assertNotIn("password", data)
        self.assertNotIn("hashed_password", data)

    @patch("app.modules.auth.repository.AuthRepository.get_user_by_id", new_callable=AsyncMock)
    async def test_me_inactive_user_returns_401(self, mock_get_user):
        from app.main import app
        from app.modules.auth.router import CurrentUser, get_current_user

        user = _fake_user(self._user_id, self._tenant_id)
        user.is_active = False
        mock_get_user.return_value = user

        async def _override():
            return CurrentUser(
                user_id=self._user_id,
                tenant_id=self._tenant_id,
                suite_role="tenant_owner",
            )

        app.dependency_overrides[get_current_user] = _override
        try:
            resp = await self.client.get("/api/v1/auth/me")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_NOT_AUTHENTICATED")

    async def test_me_without_cookie_returns_401(self):
        resp = await self.client.get("/api/v1/auth/me")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_NOT_AUTHENTICATED")
