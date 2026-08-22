from __future__ import annotations

from sqlalchemy import text

from src.common.database import engine
from src.quality.sequence_analysis import DeviceSequenceReport, analyze_sequences


def read_device_sequences() -> list[tuple[str, int]]:
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT device_id, sequence_id FROM events"))
        return [(row[0], row[1]) for row in rows]


def run() -> list[DeviceSequenceReport]:
    return analyze_sequences(read_device_sequences())


def main() -> None:
    reports = run()
    failed = [report for report in reports if not report.passed]

    for report in reports:
        print(
            f"{report.device_id}: received {report.received_count}, "
            f"expected {report.expected_count}, "
            f"missing {list(report.missing)}, "
            f"duplicates {list(report.duplicates)}"
        )

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
