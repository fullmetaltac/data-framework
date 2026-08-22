from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class ReconciliationResult:
    source_count: int
    target_count: int
    missing: frozenset[UUID] = field(default_factory=frozenset)
    duplicates: frozenset[UUID] = field(default_factory=frozenset)
    unexpected: frozenset[UUID] = field(default_factory=frozenset)

    @property
    def passed(self) -> bool:
        return not (self.missing or self.unexpected)

    def report(self) -> str:
        lines = [
            f"Source events: {self.source_count}",
            f"Target events: {self.target_count}",
            "",
            f"Missing:    {len(self.missing)}",
            f"Duplicates: {len(self.duplicates)}",
            f"Unexpected: {len(self.unexpected)}",
        ]
        return "\n".join(lines)


def reconcile(
    source_ids: Iterable[UUID], target_ids: Iterable[UUID]
) -> ReconciliationResult:
    source_ids = list(source_ids)
    target_ids = list(target_ids)

    source_set = set(source_ids)
    target_set = set(target_ids)

    duplicates = {
        event_id for event_id, count in Counter(source_ids).items() if count > 1
    }

    return ReconciliationResult(
        source_count=len(source_ids),
        target_count=len(target_ids),
        missing=frozenset(source_set - target_set),
        duplicates=frozenset(duplicates),
        unexpected=frozenset(target_set - source_set),
    )
