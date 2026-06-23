import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tests.auth.base import AuthTestCase, OWNER


def _fake_tenant(slug: str = "nxcorp") -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), slug=slug, name=slug)


def _fake_user(
    tenant_id: uuid.UUID | None = None,
    email: str = "niko@nxcorp.co",
    suite_role: str = "tenant_owner",
) -> SimpleNamespace:
    u = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=tenant_id or uuid.uuid4(),
        email=email,
        full_name="Niko Winoko",
        suite_role=suite_role,
        is_active=True,
        created_by=None,
    )
    return u


class RegisterTenantTests(AuthTestCase):

    @patch("app.modules.auth.repository.AuthRepository.get_tenant_by_slug", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.create_tenant", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.create_user", new_callable=AsyncMock)
    @patch("app.modules.auth.repository.AuthRepository.get_app_by_code", new_callable=AsyncMock)
    async def test_register_tenant_success(
        self, mock_get_app, mock_create_user, mock_create_tenant, mock_get_slug
    ):
        mock_get_slug.return_value = None
        tenant = _fake_tenant()
        mock_create_tenant.return_value = tenant
        user = _fake_user(tenant_id=tenant.id)
        mock_create_user.return_value = user
        mock_get_app.return_value = None

        resp = await self.client.post("/api/v1/auth/register-tenant", json={
            "full_name": "Niko Winoko",
            "email": "Niko@nxcorp.co",
            "password": "secret123",
            "organization_name": "nxcorp",
            "slug": "nxcorp",
        })
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["slug"], "nxcorp")
        self.assertEqual(body["user"]["suite_role"], "tenant_owner")
        self.assertEqual(body["user"]["email"], "niko@nxcorp.co")
        self.assertNotIn("password", str(body))
        self.assertNotIn("hashed_password", str(body))

    @patch("app.modules.auth.repository.AuthRepository.get_tenant_by_slug", new_callable=AsyncMock)
    async def test_register_tenant_duplicate_slug(self, mock_get_slug):
        mock_get_slug.return_value = _fake_tenant()
        resp = await self.client.post("/api/v1/auth/register-tenant", json={
            "full_name": "Niko Winoko",
            "email": "niko@nxcorp.co",
            "password": "secret123",
            "organization_name": "nxcorp",
            "slug": "nxcorp",
        })
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["error"]["code"], "AUTH_SLUG_TAKEN")

    async def test_register_tenant_weak_password_no_digit(self):
        resp = await self.client.post("/api/v1/auth/register-tenant", json={
            "full_name": "Niko Winoko",
            "email": "niko@nxcorp.co",
            "password": "onlyletters",
            "organization_name": "nxcorp",
            "slug": "nxcorp",
        })
        self.assertEqual(resp.status_code, 422)

    async def test_register_tenant_weak_password_too_short(self):
        resp = await self.client.post("/api/v1/auth/register-tenant", json={
            "full_name": "Niko Winoko",
            "email": "niko@nxcorp.co",
            "password": "sh1",
            "organization_name": "nxcorp",
            "slug": "nxcorp",
        })
        self.assertEqual(resp.status_code, 422)

    async def test_register_tenant_invalid_email(self):
        resp = await self.client.post("/api/v1/auth/register-tenant", json={
            "full_name": "Niko Winoko",
            "email": "not-an-email",
            "password": "secret123",
            "organization_name": "nxcorp",
            "slug": "nxcorp",
        })
        self.assertEqual(resp.status_code, 422)

    async def test_register_tenant_reserved_slug(self):
        resp = await self.client.post("/api/v1/auth/register-tenant", json={
            "full_name": "Niko Winoko",
            "email": "niko@nxcorp.co",
            "password": "secret123",
            "organization_name": "nxcorp",
            "slug": "admin",
        })
        self.assertEqual(resp.status_code, 422)

    async def test_register_tenant_uppercase_slug_rejected(self):
        resp = await self.client.post("/api/v1/auth/register-tenant", json={
            "full_name": "Niko Winoko",
            "email": "niko@nxcorp.co",
            "password": "secret123",
            "organization_name": "nxcorp",
            "slug": "NXCORP",
        })
        self.assertEqual(resp.status_code, 422)
