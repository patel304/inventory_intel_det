
from datetime import datetime

from sqlalchemy import (
    Integer, String, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    investigation_code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )

    alert_id: Mapped[int] = mapped_column(
        ForeignKey("shrinkage_alerts.id"),
        nullable=False,
        index=True
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30), default="PENDING", nullable=False
    )

    findings: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    resolution: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
