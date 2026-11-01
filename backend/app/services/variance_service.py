from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.inventory_math import format_quantity
from app.services.inventory_service import calculate_expected_stock


def classify_variance(variance: Decimal) -> str:
    if variance < 0:
        return "SHORTAGE"
    if variance > 0:
        return "SURPLUS"
    return "MATCHED"


def calculate_variance(
    db: Session,
    store_id: int,
    sku_id: int,
    counted_quantity,
    as_of: datetime | None = None,
) -> dict:
    expected = calculate_expected_stock(db, store_id, sku_id, as_of=as_of)
    counted = Decimal(str(counted_quantity))
    variance = counted - expected

    return {
        "store_id": store_id,
        "sku_id": sku_id,
        "expected_quantity": format_quantity(expected),
        "counted_quantity": format_quantity(counted),
        "variance_quantity": format_quantity(variance),
        "variance_type": classify_variance(variance),
        "as_of": as_of.isoformat() if as_of else None,
    }