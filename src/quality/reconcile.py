from __future__ import annotations

import json
import uuid
from uuid import UUID

from kafka import KafkaConsumer
from sqlalchemy import text

from src.common.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from src.common.database import engine
from src.quality.reconciliation import ReconciliationResult, reconcile


def read_kafka_event_ids(
    *,
    bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS,
    topic: str = KAFKA_TOPIC,
    consumer_timeout_ms: int = 5000,
) -> list[UUID]:
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=f"reconcile-{uuid.uuid4()}",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=consumer_timeout_ms,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

    event_ids: list[UUID] = []
    try:
        for message in consumer:
            raw_id = message.value.get("event_id")
            if raw_id is not None:
                event_ids.append(UUID(raw_id))
    finally:
        consumer.close()

    return event_ids


def read_db_event_ids() -> list[UUID]:
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT event_id FROM events"))
        return [row[0] for row in rows]


def run() -> ReconciliationResult:
    source_ids = read_kafka_event_ids()
    target_ids = read_db_event_ids()
    return reconcile(source_ids, target_ids)


def main() -> None:
    result = run()
    print(result.report())
    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
