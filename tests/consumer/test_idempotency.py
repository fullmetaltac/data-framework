import json
from datetime import UTC, datetime
from unittest.mock import Mock

from sqlalchemy import Connection, text

from src.common.database import engine
from src.common.models import Event
from src.consumer.main import process_message
from src.consumer.repository import EventRepository


def test_processing_the_same_event_twice_stores_it_once(
    db_connection: Connection,
) -> None:
    event = Event(
        device_id="idempotency-test-sensor",
        sequence_id=1,
        event_time=datetime.now(UTC),
        temperature=21.0,
        humidity=45.0,
        pressure=1005.0,
        status="OK",
    )
    message = json.loads(event.model_dump_json())
    repository = EventRepository()
    dlq_producer = Mock()

    try:
        first_outcome = process_message(
            message,
            repository=repository,
            dlq_producer=dlq_producer,
            source_topic="events",
        )
        # Simulates Kafka redelivering the message after a crash between the
        # DB write and the offset commit: the consumer sees it again.
        second_outcome = process_message(
            message,
            repository=repository,
            dlq_producer=dlq_producer,
            source_topic="events",
        )

        stored = db_connection.execute(
            text("SELECT COUNT(*) FROM events WHERE event_id = :event_id"),
            {"event_id": str(event.event_id)},
        ).scalar()

        assert first_outcome == "saved"
        assert second_outcome == "duplicate"
        assert stored == 1
        dlq_producer.send.assert_not_called()
    finally:
        with engine.begin() as cleanup:
            cleanup.execute(
                text("DELETE FROM events WHERE event_id = :event_id"),
                {"event_id": str(event.event_id)},
            )
