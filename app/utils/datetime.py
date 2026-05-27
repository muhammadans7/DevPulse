from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current UTC datetime — use as default_factory for timestamp fields."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
