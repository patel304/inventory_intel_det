
from datetime import datetime

from sqlalchemy import (
    Integer, String, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id"),
        nullable=False,
        index=True
    )

    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    performed_by: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    event_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
