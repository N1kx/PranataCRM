from tests.common import MockedAppTestCase

OWNER = {
    "full_name": "Niko Winoko",
    "email": "niko@nxcorp.co",
    "password": "secret123",
    "organization_name": "nxcorp",
    "slug": "nxcorp",
}


class AuthTestCase(MockedAppTestCase):
    """Base for async auth tests. Redis and DB are mocked."""

    async def register_owner(self, **overrides):
        payload = {**OWNER, **overrides}
        return await self.client.post("/api/v1/auth/register-tenant", json=payload)

    async def login_owner(
        self,
        slug: str = "nxcorp",
        email: str = OWNER["email"],
        password: str = OWNER["password"],
    ):
        return await self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            headers={"X-Tenant-Slug": slug},
        )
