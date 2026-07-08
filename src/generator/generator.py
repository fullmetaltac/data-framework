import random
from datetime import datetime, timezone

from .models import Event


class EventGenerator:
    def generate(self) -> Event:
        return Event(
            device_id=f"sensor-{random.randint(1, 20):02d}",
            event_time=datetime.now(timezone.utc),
            temperature=round(random.uniform(-10.0, 40.0), 1),
            humidity=round(random.uniform(20.0, 90.0), 1),
            pressure=round(random.uniform(980.0, 1040.0), 1),
            status="OK",
        )
