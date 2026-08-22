from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceSequenceReport:
    device_id: str
    received_count: int
    expected_count: int
    missing: tuple[int, ...]
    duplicates: tuple[int, ...]

    @property
    def passed(self) -> bool:
        return not (self.missing or self.duplicates)


def analyze_sequences(
    readings: Iterable[tuple[str, int]],
) -> list[DeviceSequenceReport]:
    sequences_by_device: dict[str, list[int]] = defaultdict(list)
    for device_id, sequence_id in readings:
        sequences_by_device[device_id].append(sequence_id)

    reports = []
    for device_id in sorted(sequences_by_device):
        counts = Counter(sequences_by_device[device_id])
        duplicates = tuple(
            sorted(sequence_id for sequence_id, count in counts.items() if count > 1)
        )

        seen = sorted(counts)
        expected = set(range(seen[0], seen[-1] + 1))
        missing = tuple(sorted(expected - set(seen)))

        reports.append(
            DeviceSequenceReport(
                device_id=device_id,
                received_count=len(sequences_by_device[device_id]),
                expected_count=len(expected),
                missing=missing,
                duplicates=duplicates,
            )
        )

    return reports
