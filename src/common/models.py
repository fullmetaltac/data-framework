from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    device_id: str
    event_time: datetime
    temperature: float
    humidity: float
    pressure: float
    status: str
