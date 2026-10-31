
from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PromotionSKU(Base):
    __tablename__ = "promotion_skus"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    promotion_id: Mapped[int] = mapped_column(
        ForeignKey("promotions.id"), nullable=False
    )

    sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "promotion_id",
            "sku_id",
            name="uq_promotion_sku"
        ),
    )
