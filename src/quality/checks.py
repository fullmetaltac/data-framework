from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import Connection, text

from src.common.database import engine

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _identifier(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return value


@dataclass(frozen=True)
class CheckResult:
    check: str
    invalid_count: int

    @property
    def passed(self) -> bool:
        return self.invalid_count == 0


@dataclass(frozen=True)
class Check:
    table: str
    name: str
    query: str
    parameters: dict[str, object]
    failure_message: str

    @classmethod
    def not_null(cls, column: str, *, table: str = "events") -> Check:
        table, column = _identifier(table), _identifier(column)
        return cls(
            table,
            f"{column}.not_null",
            f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL",
            {},
            f"Found {{count}} rows with NULL {column}",
        )

    @classmethod
    def range(
        cls, column: str, minimum: object, maximum: object, *, table: str = "events"
    ) -> Check:
        if minimum > maximum:  # type: ignore[operator]
            raise ValueError("minimum must not be greater than maximum")
        table, column = _identifier(table), _identifier(column)
        return cls(
            table,
            f"{column}.range",
            f"SELECT COUNT(*) FROM {table} "
            f"WHERE {column} NOT BETWEEN :minimum AND :maximum",
            {"minimum": minimum, "maximum": maximum},
            f"Found {{count}} rows with {column} outside [{minimum}, {maximum}]",
        )

    @classmethod
    def unique(cls, columns: Sequence[str], *, table: str = "events") -> Check:
        if not columns:
            raise ValueError("unique requires at least one column")
        table = _identifier(table)
        safe_columns = tuple(_identifier(column) for column in columns)
        joined = ", ".join(safe_columns)
        return cls(
            table,
            f"{joined}.unique",
            "SELECT COUNT(*) FROM ("
            f"SELECT {joined} FROM {table} GROUP BY {joined} "
            "HAVING COUNT(*) > 1"
            ") AS duplicate_groups",
            {},
            f"Found {{count}} duplicate ({joined}) groups",
        )

    @classmethod
    def freshness(
        cls,
        column: str,
        *,
        minutes: int,
        reference: str = "created_at",
        table: str = "events",
    ) -> Check:
        if minutes <= 0:
            raise ValueError("minutes must be greater than zero")
        table = _identifier(table)
        column, reference = _identifier(column), _identifier(reference)
        return cls(
            table,
            f"{column}.freshness",
            f"SELECT COUNT(*) FROM {table} "
            f"WHERE {column} < {reference} - :window OR {column} > {reference}",
            {"window": timedelta(minutes=minutes)},
            f"Found {{count}} rows outside the {minutes}-minute freshness window",
        )

    def run(self, connection: Connection | None = None) -> CheckResult:
        if connection is None:
            with engine.connect() as managed_connection:
                return self.run(managed_connection)
        invalid_count = int(connection.scalar(text(self.query), self.parameters) or 0)
        result = CheckResult(self.name, invalid_count)
        if not result.passed:
            raise AssertionError(self.failure_message.format(count=invalid_count))
        return result
