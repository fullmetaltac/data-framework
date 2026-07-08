from sqlalchemy import Connection

from src.quality import Check


def test_temperature_is_in_valid_range(db_connection: Connection) -> None:
    Check.range("temperature", -40, 80).run(db_connection)
