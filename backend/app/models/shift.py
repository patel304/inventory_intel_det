from sqlalchemy import String, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    shift_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    shift_name: Mapped[str] = mapped_column(String(100), nullable=False)

    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)