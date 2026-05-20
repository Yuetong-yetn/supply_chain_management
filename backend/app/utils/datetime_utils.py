from datetime import datetime, timezone


def now_local() -> datetime:
    return datetime.now(timezone.utc).astimezone()
