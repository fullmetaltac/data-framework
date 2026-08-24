from sqlalchemy import Connection, text


def test_only_known_statuses_are_used(db_connection: Connection) -> None:
    invalid_statuses = db_connection.execute(text("""
            SELECT status, COUNT(*) AS event_count
            FROM events
            WHERE status IS NULL
               OR status NOT IN ('OK', 'WARNING', 'ERROR')
            GROUP BY status
            ORDER BY status
            """)).all()

    assert not invalid_statuses, f"Found unsupported statuses: {invalid_statuses}"
