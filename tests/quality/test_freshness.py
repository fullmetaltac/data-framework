from sqlalchemy import Connection, text


def test_events_are_within_five_minute_freshness_window(
    db_connection: Connection,
) -> None:
    invalid_count = db_connection.scalar(
        text(
            """
            SELECT COUNT(*)
            FROM events
            WHERE event_time < created_at - INTERVAL '5 minutes'
               OR event_time > created_at
            """
        )
    )

    assert invalid_count == 0, (
        f"Found {invalid_count} events delivered late or from the future"
    )
