
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Return(Base):
    __tablename__ = "returns"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    return_code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), nullable=False
    )

    sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id"), nullable=False
    )

    original_sale_movement_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_movements.id"), nullable=True
    )

    return_movement_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_movements.id"), nullable=True
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False
    )

    return_reason: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    return_status: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    returned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
