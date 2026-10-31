
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Integer, String, DateTime, Numeric,
    ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    movement_code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), nullable=False
    )

    sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id"), nullable=False
    )

    employee_role_id: Mapped[int] = mapped_column(
        ForeignKey("employee_roles.id"), nullable=True
    )

    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shifts.id"), nullable=True
    )

    movement_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False
    )

    reference_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    transfer_group_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )

    effective_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )

    source_system: Mapped[str] = mapped_column(
        String(50), default="SYNTHETIC", nullable=False
    )

    __table_args__ = (
        Index(
            "ix_movement_store_sku_effective",
            "store_id",
            "sku_id",
            "effective_at"
        ),
    )
