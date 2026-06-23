import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.auth.base import AuthTestCase, OWNER


def _fake_user(email: str = "niko@nxcorp.co", suite_role: str = "tenant_owner") -> SimpleNamespace:
    from app.shared.security import hash_password
    return SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email=email,
        full_name="Niko Winoko",
        hashed_password=hash_password("secret123"),
        suite_role=suite_role,
        is_active=True,
    )


def _fake_tenant(slug: str = "nxcorp") -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), slug=slug)


class LoginTests(AuthTestCase):

    @patch("app.modules.auth.repository.AuthRepository.get_tenant_by_slug", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.get_user_by_email", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.store_refresh_token", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.update_last_login", new_callable=AsyncMock)
    async def test_login_success(
        self, mock_update, mock_store_rt, mock_get_user, mock_get_tenant
    ):
        tenant = _fake_tenant()
        user = _fake_user()
        user.tenant_id = tenant.id
        mock_get_tenant.return_value = tenant
        mock_get_user.return_value = user

        resp = await self.client.post(
            "/api/v1/auth/login",
            json={"email": OWNER["email"], "password": OWNER["password"]},
            headers={"X-Tenant-Slug": "nxcorp"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", resp.cookies)
        self.assertIn("refresh_token", resp.cookies)
        body = resp.json()
        self.assertEqual(body["email"], "niko@nxcorp.co")

    @patch("app.modules.auth.repository.AuthRepository.get_tenant_by_slug", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.get_user_by_email", new_callable=AsyncMock)
    async def test_login_wrong_password_same_message_as_unknown_email(
        self, mock_get_user, mock_get_tenant
    ):
        tenant = _fake_tenant()
        user = _fake_user()
        user.tenant_id = tenant.id
        mock_get_tenant.return_value = tenant
        # First call returns user (but password wrong), second returns None (unknown email)
        mock_get_user.side_effect = [user, None]

        r1 = await self.client.post(
            "/api/v1/auth/login",
            json={"email": OWNER["email"], "password": "wrongpass1"},
            headers={"X-Tenant-Slug": "nxcorp"},
        )
        r2 = await self.client.post(
            "/api/v1/auth/login",
            json={"email": "nouser@nxcorp.co", "password": "whatever1"},
            headers={"X-Tenant-Slug": "nxcorp"},
        )
        self.assertEqual(r1.status_code, 401)
        self.assertEqual(r2.status_code, 401)
        self.assertEqual(r1.json()["error"]["code"], "AUTH_INVALID_CREDENTIALS")
        self.assertEqual(r1.json()["error"]["code"], r2.json()["error"]["code"])
        self.assertEqual(r1.json()["error"]["message"], r2.json()["error"]["message"])

    @patch("app.modules.auth.repository.AuthRepository.get_tenant_by_slug", new_callable=AsyncMock)
    async def test_login_unknown_tenant(self, mock_get_tenant):
        mock_get_tenant.return_value = None
        resp = await self.client.post(
            "/api/v1/auth/login",
            json={"email": OWNER["email"], "password": OWNER["password"]},
            headers={"X-Tenant-Slug": "doesnotexist"},
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_TENANT_NOT_FOUND")
