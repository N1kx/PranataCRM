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


def make_mock_redis() -> MagicMock:
    """Return a MagicMock that quacks like the redis.asyncio client, with
    every method the app actually awaits pre-stubbed as an AsyncMock (plain
    MagicMock attributes are not awaitable and would raise TypeError)."""
    redis = MagicMock()
    redis.ping = AsyncMock()
    redis.aclose = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    return redis


class MockedAppTestCase(unittest.IsolatedAsyncioTestCase):
    """Base for async API tests. Redis and DB are mocked — no real services needed."""

    async def asyncSetUp(self) -> None:
        self._redis_patcher = patch("app.main.aioredis.from_url", return_value=make_mock_redis())
        self._db_patcher = patch("app.database.get_db", side_effect=_mock_get_db)
        self._redis_patcher.start()
        self._db_patcher.start()
        from app.main import app

        # The lifespan (where app.state.redis is normally assigned) never
        # runs under a bare ASGITransport/AsyncClient — set it directly so
        # any endpoint depending on app.shared.redis.get_redis resolves
        # without needing a real startup event. Previously nothing in the
        # app actually read app.state.redis outside /health's try/except
        # Exception: pass, so this gap was invisible until the geo module
        # (issue #26) added the first real dependency on it.
        app.state.redis = make_mock_redis()

        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://nxcorp.localhost")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        self._redis_patcher.stop()
        self._db_patcher.stop()
