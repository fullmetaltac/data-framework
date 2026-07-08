from sqlalchemy import Connection

from src.quality import Check


def test_temperature_has_no_nulls(db_connection: Connection) -> None:
    Check.not_null("temperature").run(db_connection)
