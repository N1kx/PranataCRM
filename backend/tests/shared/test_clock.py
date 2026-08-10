import unittest
from datetime import datetime, timezone

from app.shared.clock import utc_now, utc_today


class ClockTests(unittest.TestCase):
    """app.shared.clock is the backend's only sanctioned clock, so that no
    module reads the process/OS timezone by accident (see issue #48). These
    tests pin the two guarantees callers rely on: utc_now() is always
    timezone-aware UTC, and utc_today() is that instant's calendar date.

    Neither test can catch a regression to date.today()/datetime.now() on its
    own — on a UTC machine those return the same values, and the container is
    pinned to TZ=UTC precisely so it stays that way. Enforcement lives in the
    ruff DTZ ruleset (pyproject.toml), which rejects both calls at lint time.
    """

    def test_utc_now_is_timezone_aware_utc(self) -> None:
        self.assertEqual(utc_now().utcoffset(), timezone.utc.utcoffset(None))

    def test_utc_today_matches_utc_date(self) -> None:
        # Sampled either side of the call so a UTC midnight landing mid-test
        # can't fail it: the result must match one of the two samples.
        before = datetime.now(timezone.utc).date()
        result = utc_today()
        after = datetime.now(timezone.utc).date()
        self.assertIn(result, (before, after))
