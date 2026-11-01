from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.inventory_math import signed_quantity
from app.models import InventoryMovement


def calculate_expected_stock(
    db: Session,
    store_id: int,
    sku_id: int,
    as_of: datetime | None = None,
) -> Decimal:
    """
    Expected stock for one store/SKU.

    Expected Stock =
      Opening Balance + Receipts + Returns In + Transfers In
      - Sales - Transfers Out - Damage
      + Adjustments In - Adjustments Out

    If as_of is provided, only movements with effective_at <= as_of are included.
    Quantities are treated as positive magnitudes.
    """
    query = db.query(
        InventoryMovement.movement_type,
        func.sum(InventoryMovement.quantity).label("total_quantity"),
    ).filter(
        InventoryMovement.store_id == store_id,
        InventoryMovement.sku_id == sku_id,
    )

    if as_of is not None:
        query = query.filter(InventoryMovement.effective_at <= as_of)

    movements = query.group_by(InventoryMovement.movement_type).all()

    expected_stock = Decimal("0")
    for movement_type, total_quantity in movements:
        expected_stock += signed_quantity(movement_type, total_quantity)

    return expected_stock
