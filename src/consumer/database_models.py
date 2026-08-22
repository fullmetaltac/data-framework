from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, unique=True)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    sequence_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    humidity: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    pressure: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    status: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
