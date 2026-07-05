"""US market trading-day helper (static NYSE holiday list, stdlib only).

Update the holiday table once a year (task: yearly, 10 minutes).
"""

from __future__ import annotations

from datetime import date

# NYSE full-day holidays. Source: nyse.com official calendar.
_HOLIDAYS: set[str] = {
    # 2026
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # Martin Luther King Jr. Day
    "2026-02-16",  # Washington's Birthday
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day
    "2026-06-19",  # Juneteenth
    "2026-07-03",  # Independence Day (observed)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-12-25",  # Christmas
    # 2027
    "2027-01-01",
    "2027-01-18",
    "2027-02-15",
    "2027-03-26",
    "2027-05-31",
    "2027-06-18",  # Juneteenth (observed)
    "2027-07-05",  # Independence Day (observed)
    "2027-09-06",
    "2027-11-25",
    "2027-12-24",  # Christmas (observed)
}


def is_trading_day(d: date) -> bool:
    if d.weekday() >= 5:  # Sat/Sun
        return False
    return d.isoformat() not in _HOLIDAYS


def holiday_name(d: date) -> str | None:
    return "US market holiday" if d.isoformat() in _HOLIDAYS else None
