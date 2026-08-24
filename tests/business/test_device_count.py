from sqlalchemy import Connection, text


def test_device_count_is_in_expected_range(db_connection: Connection) -> None:
    device_count = db_connection.scalar(text("""
            SELECT COUNT(DISTINCT device_id)
            FROM events
            WHERE device_id <> ''
            """))

    assert (
        1 <= device_count <= 20
    ), f"Expected between 1 and 20 devices, found {device_count}"
