from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    device_id: str
    event_time: datetime
    temperature: float
    humidity: float
    pressure: float
    status: str
