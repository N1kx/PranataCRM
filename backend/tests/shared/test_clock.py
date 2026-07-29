import unittest
from datetime import datetime, timezone

from app.shared.clock import utc_today


class UtcTodayTests(unittest.TestCase):
    def test_utc_today_matches_utc_date(self) -> None:
        self.assertEqual(utc_today(), datetime.now(timezone.utc).date())
