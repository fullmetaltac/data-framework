from unittest.mock import Mock

import pytest

from src.quality import Check, Table, expect


def connection_returning(count: int) -> Mock:
    connection = Mock()
    connection.scalar.return_value = count
    return connection


def test_check_passes_and_returns_a_result() -> None:
    result = Check.not_null("device_id").run(connection_returning(0))
    assert result.passed
    assert result.invalid_count == 0


def test_check_explains_a_failure() -> None:
    with pytest.raises(AssertionError, match="3 rows with NULL device_id"):
        Check.not_null("device_id").run(connection_returning(3))


def test_table_runs_declarative_check_chain() -> None:
    connection = connection_returning(0)
    results = (
        Table("events")
        .not_null("device_id")
        .range("temperature", -40, 80)
        .unique("device_id", "event_time")
        .run(connection)
    )
    assert len(results) == 3
    assert connection.scalar.call_count == 3


def test_expect_column_dsl() -> None:
    result = (
        expect(table="events")
        .column("temperature")
        .to_be_between(-40, 80, connection_returning(0))
    )
    assert result.passed


def test_identifiers_cannot_inject_sql() -> None:
    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        Check.not_null("device_id; DROP TABLE events")
