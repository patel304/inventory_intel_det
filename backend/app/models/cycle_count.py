
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, DateTime, Numeric, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CycleCount(Base):
    __tablename__ = "cycle_counts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    count_code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), nullable=False
    )

    sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id"), nullable=False
    )

    employee_role_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee_roles.id"), nullable=True
    )

    shift_id: Mapped[int | None] = mapped_column(
        ForeignKey("shifts.id"), nullable=True
    )

    counted_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False
    )

    counted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )

    count_status: Mapped[str] = mapped_column(
        String(30), default="COMPLETED", nullable=False
    )
