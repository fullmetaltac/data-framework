import random
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from src.common.models import Event


class InvalidEventType(StrEnum):
    NULL_TEMPERATURE = "null_temperature"
    HIGH_HUMIDITY = "high_humidity"
    LOW_TEMPERATURE = "low_temperature"
    EMPTY_DEVICE_ID = "empty_device_id"
    FUTURE_EVENT = "future_event"
    DUPLICATE = "duplicate"
    OLD_EVENT = "old_event"


class EventGenerator:
    def __init__(self, invalid_probability: float = 0.05) -> None:
        if not 0.0 <= invalid_probability <= 1.0:
            raise ValueError("invalid_probability must be between 0 and 1.")

        self.invalid_probability = invalid_probability
        self._last_event: Event | None = None
        self._sequence_counters: dict[str, int] = {}

    def generate(self) -> Event:
        event = self._generate_valid_event()

        if random.random() < self.invalid_probability:
            event = self._make_invalid(event)

        self._last_event = event.model_copy(deep=True)
        return event

    def _generate_valid_event(self) -> Event:
        device_id = f"sensor-{random.randint(1, 20):02d}"
        return Event(
            device_id=device_id,
            sequence_id=self._next_sequence_id(device_id),
            event_time=datetime.now(UTC),
            temperature=round(random.uniform(-10.0, 40.0), 1),
            humidity=round(random.uniform(20.0, 90.0), 1),
            pressure=round(random.uniform(980.0, 1040.0), 1),
            status="OK",
        )

    def _next_sequence_id(self, device_id: str) -> int:
        sequence_id = self._sequence_counters.get(device_id, 0) + 1
        self._sequence_counters[device_id] = sequence_id
        return sequence_id

    def _make_invalid(self, event: Event) -> Event:
        error_types = list(InvalidEventType)
        if self._last_event is None:
            error_types.remove(InvalidEventType.DUPLICATE)

        error_type = random.choice(error_types)

        if error_type == InvalidEventType.NULL_TEMPERATURE:
            return event.model_copy(update={"temperature": None})
        if error_type == InvalidEventType.HIGH_HUMIDITY:
            return event.model_copy(update={"humidity": 150.0})
        if error_type == InvalidEventType.LOW_TEMPERATURE:
            return event.model_copy(update={"temperature": -100.0})
        if error_type == InvalidEventType.EMPTY_DEVICE_ID:
            return event.model_copy(update={"device_id": ""})
        if error_type == InvalidEventType.FUTURE_EVENT:
            return event.model_copy(
                update={"event_time": event.event_time + timedelta(days=2)}
            )
        if error_type == InvalidEventType.DUPLICATE:
            assert self._last_event is not None
            return self._last_event.model_copy(deep=True)

        return event.model_copy(
            update={"event_time": event.event_time - timedelta(days=7)}
        )
