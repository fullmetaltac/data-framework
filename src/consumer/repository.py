from sqlalchemy import text

from src.common.database import get_session
from src.common.models import Event


class EventRepository:
    def save(self, event: Event) -> None:
        query = text(
            """
            INSERT INTO events (
                device_id,
                event_time,
                temperature,
                humidity,
                pressure,
                status
            )
            VALUES (
                :device_id,
                :event_time,
                :temperature,
                :humidity,
                :pressure,
                :status
            )
            """
        )

        with get_session() as session:
            session.execute(query, event.model_dump())
