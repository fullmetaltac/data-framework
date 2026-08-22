from sqlalchemy import Connection, inspect


def test_events_table_has_expected_columns(db_connection: Connection) -> None:
    columns = {
        column["name"]: column
        for column in inspect(db_connection).get_columns("events")
    }

    assert set(columns) == {
        "id",
        "event_id",
        "device_id",
        "sequence_id",
        "event_time",
        "temperature",
        "humidity",
        "pressure",
        "status",
        "created_at",
    }


def test_required_columns_are_not_nullable(db_connection: Connection) -> None:
    columns = {
        column["name"]: column
        for column in inspect(db_connection).get_columns("events")
    }

    for column_name in (
        "id",
        "event_id",
        "device_id",
        "sequence_id",
        "event_time",
        "created_at",
    ):
        assert not columns[column_name][
            "nullable"
        ], f"events.{column_name} must be NOT NULL"
