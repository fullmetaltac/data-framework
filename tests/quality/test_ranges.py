from sqlalchemy import Connection, text


def test_temperature_is_in_valid_range(db_connection: Connection) -> None:
    invalid_count = db_connection.scalar(
        text(
            """
            SELECT COUNT(*)
            FROM events
            WHERE temperature NOT BETWEEN -40 AND 80
            """
        )
    )

    assert invalid_count == 0, (
        f"Found {invalid_count} events with temperature outside [-40, 80]"
    )
