from sqlalchemy import Connection

from src.quality import Check


def test_device_and_event_time_are_unique(db_connection: Connection) -> None:
    Check.unique(["device_id", "event_time"]).run(db_connection)
