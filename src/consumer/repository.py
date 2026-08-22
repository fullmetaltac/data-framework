from src.common.database import get_session
from src.common.models import Event
from src.consumer.database_models import EventRecord


class EventRepository:
    def save(self, event: Event) -> None:
        record = EventRecord(
            event_id=event.event_id,
            device_id=event.device_id,
            event_time=event.event_time,
            temperature=event.temperature,
            humidity=event.humidity,
            pressure=event.pressure,
            status=event.status,
        )

        with get_session() as session:
            session.add(record)
