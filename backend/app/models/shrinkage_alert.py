
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Integer, String, DateTime, Numeric, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ShrinkageAlert(Base):
    __tablename__ = "shrinkage_alerts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    alert_code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), nullable=False
    )

    sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id"), nullable=False
    )

    cycle_count_id: Mapped[int | None] = mapped_column(
        ForeignKey("cycle_counts.id"), nullable=True
    )

    detection_rule: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )

    expected_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 3), nullable=True
    )

    observed_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 3), nullable=True
    )

    variance_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 3), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30), default="OPEN", nullable=False
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )

    __table_args__ = (
        Index(
            "ix_alert_store_status",
            "store_id",
            "status"
        ),
    )
