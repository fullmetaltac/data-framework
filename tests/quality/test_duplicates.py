from sqlalchemy import Connection, text


def test_device_and_event_time_are_unique(db_connection: Connection) -> None:
    duplicate_count = db_connection.scalar(
        text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT device_id, event_time
                FROM events
                GROUP BY device_id, event_time
                HAVING COUNT(*) > 1
            ) AS duplicates
            """
        )
    )

    assert duplicate_count == 0, (
        f"Found {duplicate_count} duplicate (device_id, event_time) groups"
    )
