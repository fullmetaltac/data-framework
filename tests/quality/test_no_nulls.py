from sqlalchemy import Connection, text


def test_temperature_has_no_nulls(db_connection: Connection) -> None:
    null_count = db_connection.scalar(
        text("SELECT COUNT(*) FROM events WHERE temperature IS NULL")
    )

    assert null_count == 0, f"Found {null_count} events with NULL temperature"
