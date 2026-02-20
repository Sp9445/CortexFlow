from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> datetime:
    """Return current time in +5:30 timezone."""
    return datetime.now(IST)