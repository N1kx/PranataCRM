import unittest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient


def make_mock_session() -> MagicMock:
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
    yield make_mock_session()


class MockedAppTestCase(unittest.IsolatedAsyncioTestCase):
    """Base for async API tests. Redis and DB are mocked — no real services needed."""

    async def asyncSetUp(self) -> None:
        self._redis_patcher = patch(
            "app.main.aioredis.from_url",
            return_value=MagicMock(ping=AsyncMock(), aclose=AsyncMock()),
        )
        self._db_patcher = patch("app.database.get_db", side_effect=_mock_get_db)
        self._redis_patcher.start()
        self._db_patcher.start()
        from app.main import app
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://nxcorp.localhost")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        self._redis_patcher.stop()
        self._db_patcher.stop()
