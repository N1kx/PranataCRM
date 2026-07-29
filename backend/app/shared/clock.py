"""Clock access for the whole backend.

Everything that needs the current time or date goes through here, so no module
can accidentally read the process/OS timezone. Business dates are decided in
UTC; see the per-user-timezone follow-up issue for why that is a deliberate
interim choice rather than the final answer.
"""
from datetime import date, datetime, timezone


def utc_now() -> datetime:
    """Current instant, always timezone-aware UTC."""
    return datetime.now(timezone.utc)


def utc_today() -> date:
    """Today's date in UTC.

    Deliberately NOT `date.today()`, which silently follows whatever timezone
    the container's OS is configured with.
    """
    return utc_now().date()
