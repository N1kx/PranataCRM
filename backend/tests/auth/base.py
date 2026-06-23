import unittest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient

OWNER = {
    "full_name": "Niko Winoko",
    "email": "niko@nxcorp.co",
    "password": "secret123",
    "organization_name": "nxcorp",
    "slug": "nxcorp",
}


def _make_mock_session() -> MagicMock:
    """Return a MagicMock that quacks like an AsyncSession."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@asynccontextmanager
async def _mock_get_db():
    yield _make_mock_session()


_redis_patcher = patch(
    "app.main.aioredis.from_url",
    return_value=MagicMock(ping=AsyncMock(), aclose=AsyncMock()),
)
_db_patcher = patch("app.database.get_db", side_effect=_mock_get_db)


class AuthTestCase(unittest.IsolatedAsyncioTestCase):
    """Base for async auth tests. Redis and DB are mocked — no real services needed."""

    async def asyncSetUp(self) -> None:
        _redis_patcher.start()
        _db_patcher.start()
        from app.main import app
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://nxcorp.localhost")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        _redis_patcher.stop()
        _db_patcher.stop()

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
