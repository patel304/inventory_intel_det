
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    promotion_code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    discount_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )

    end_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30), default="SCHEDULED", nullable=False
    )
