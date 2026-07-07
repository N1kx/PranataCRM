import unittest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient


def _make_mock_session() -> MagicMock:
    """Return a MagicMock that quacks like an AsyncSession."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.delete = AsyncMock()
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


class ContactsTestCase(unittest.IsolatedAsyncioTestCase):
    """Base for async contacts tests. Redis and DB are mocked — no real services needed."""

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
