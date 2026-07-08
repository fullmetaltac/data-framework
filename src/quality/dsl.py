from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import Connection

from .checks import Check, CheckResult


@dataclass(frozen=True)
class ColumnExpectation:
    table: str
    column_name: str

    def not_to_be_null(self, connection: Connection | None = None) -> CheckResult:
        return Check.not_null(self.column_name, table=self.table).run(connection)

    def to_be_between(
        self, minimum: object, maximum: object, connection: Connection | None = None
    ) -> CheckResult:
        return Check.range(
            self.column_name, minimum, maximum, table=self.table
        ).run(connection)


@dataclass
class Table:
    name: str
    checks: list[Check] = field(default_factory=list)

    def not_null(self, column: str) -> Table:
        self.checks.append(Check.not_null(column, table=self.name))
        return self

    def range(self, column: str, minimum: object, maximum: object) -> Table:
        self.checks.append(Check.range(column, minimum, maximum, table=self.name))
        return self

    def unique(self, *columns: str) -> Table:
        self.checks.append(Check.unique(columns, table=self.name))
        return self

    def freshness(
        self, column: str, *, minutes: int, reference: str = "created_at"
    ) -> Table:
        self.checks.append(
            Check.freshness(
                column, minutes=minutes, reference=reference, table=self.name
            )
        )
        return self

    def run(self, connection: Connection | None = None) -> list[CheckResult]:
        return [check.run(connection) for check in self.checks]


@dataclass(frozen=True)
class _Expectation:
    table: str

    def column(self, name: str) -> ColumnExpectation:
        return ColumnExpectation(self.table, name)


def expect(*, table: str) -> _Expectation:
    return _Expectation(table)
