from typing import Any
from unittest.mock import Mock

from sqlalchemy.exc import IntegrityError

from src.consumer.main import process_message


def valid_message() -> dict[str, Any]:
    return {
        "event_id": "11111111-1111-1111-1111-111111111111",
        "device_id": "sensor-01",
        "event_time": "2026-01-01T00:00:00Z",
        "temperature": 20.0,
        "humidity": 50.0,
        "pressure": 1000.0,
        "status": "OK",
    }


def test_valid_event_is_saved() -> None:
    repository = Mock()
    dlq_producer = Mock()

    status = process_message(
        valid_message(),
        repository=repository,
        dlq_producer=dlq_producer,
        source_topic="events",
    )

    assert status == "saved"
    repository.save.assert_called_once()
    dlq_producer.send.assert_not_called()


def test_invalid_events_are_sent_to_dlq() -> None:
    repository = Mock()
    dlq_producer = Mock()
    message = valid_message()
    message["temperature"] = None

    status = process_message(
        message,
        repository=repository,
        dlq_producer=dlq_producer,
        source_topic="events",
    )

    assert status == "invalid"
    repository.save.assert_not_called()
    dlq_producer.send.assert_called_once()

    call_kwargs = dlq_producer.send.call_args.kwargs
    assert call_kwargs["original_message"] == message
    assert call_kwargs["source_topic"] == "events"
    assert "temperature" in call_kwargs["error"]


def test_duplicate_event_is_skipped_without_dlq() -> None:
    repository = Mock()
    repository.save.side_effect = IntegrityError("stmt", {}, Exception("dup"))
    dlq_producer = Mock()

    status = process_message(
        valid_message(),
        repository=repository,
        dlq_producer=dlq_producer,
        source_topic="events",
    )

    assert status == "duplicate"
    dlq_producer.send.assert_not_called()
