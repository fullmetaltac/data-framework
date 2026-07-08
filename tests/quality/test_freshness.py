from sqlalchemy import Connection

from src.quality import Check


def test_events_are_within_five_minute_freshness_window(
    db_connection: Connection,
) -> None:
    Check.freshness("event_time", minutes=5).run(db_connection)
