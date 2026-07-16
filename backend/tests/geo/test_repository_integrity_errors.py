"""GeoRepository must translate a UNIQUE-constraint violation on
create/update state/city into a clean GeoValidationError (422), not let an
aborted-transaction IntegrityError bubble up as an unhandled 500 (issue #26
PR review, finding #3).

GeoService's own pre-check only looks at *active* rows, so a name collision
with a deactivated row (or a concurrent request) only ever surfaces at the
DB constraint — these tests exercise that path directly against the
repository with a mocked session, since triggering a real UNIQUE violation
needs a real Postgres instance.
"""
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.exc import IntegrityError

from app.modules.geo.exceptions import GeoValidationError
from app.modules.geo.models import GeoCity, GeoState
from app.modules.geo.repository import GeoRepository


def _mock_session_that_fails_flush() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock(side_effect=IntegrityError("INSERT", {}, Exception("unique violation")))
    session.rollback = AsyncMock()
    return session


class GeoRepositoryIntegrityErrorTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_state_translates_integrity_error_and_rolls_back(self) -> None:
        session = _mock_session_that_fails_flush()
        repo = GeoRepository(session)

        with self.assertRaises(GeoValidationError):
            await repo.create_state({"country_code": "ID", "name": "Jawa Barat", "code": None})

        session.rollback.assert_awaited_once()

    async def test_update_state_translates_integrity_error_and_rolls_back(self) -> None:
        session = _mock_session_that_fails_flush()
        repo = GeoRepository(session)
        state = GeoState(
            id=uuid.uuid4(), country_code="ID", name="Old Name", code=None, is_active=True,
        )

        with self.assertRaises(GeoValidationError):
            await repo.update_state(state, {"name": "Jawa Timur"})

        session.rollback.assert_awaited_once()

    async def test_create_city_translates_integrity_error_and_rolls_back(self) -> None:
        session = _mock_session_that_fails_flush()
        repo = GeoRepository(session)

        with self.assertRaises(GeoValidationError):
            await repo.create_city({"state_id": uuid.uuid4(), "country_code": "ID", "name": "Bandung"})

        session.rollback.assert_awaited_once()

    async def test_update_city_translates_integrity_error_and_rolls_back(self) -> None:
        session = _mock_session_that_fails_flush()
        repo = GeoRepository(session)
        city = GeoCity(
            id=uuid.uuid4(), state_id=uuid.uuid4(), country_code="ID", name="Old City", is_active=True,
        )

        with self.assertRaises(GeoValidationError):
            await repo.update_city(city, {"name": "New City"})

        session.rollback.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
