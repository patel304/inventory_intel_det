
from decimal import Decimal
from sqlalchemy import func

from app.models import InventoryMovement

INCREASE_TYPES = {
    "OPENING_BALANCE",
    "RECEIPT",
    "RETURN_IN",
    "TRANSFER_IN",
}

DECREASE_TYPES = {
    "SALE",
    "DAMAGE",
    "TRANSFER_OUT",
}


def calculate_expected_stock(db, store_id, sku_id):
    """
    Calculate expected inventory for one store and SKU.
    Movement quantities are treated as positive magnitudes.
    """

    movements = (
        db.query(
            InventoryMovement.movement_type,
            func.sum(InventoryMovement.quantity).label("total_quantity"),
        )
        .filter(
            InventoryMovement.store_id == store_id,
            InventoryMovement.sku_id == sku_id,
        )
        .group_by(InventoryMovement.movement_type)
        .all()
    )

    expected_stock = Decimal("0")

    for movement_type, total_quantity in movements:
        quantity = Decimal(str(total_quantity or 0))

        if movement_type in INCREASE_TYPES:
            expected_stock += quantity

        elif movement_type in DECREASE_TYPES:
            expected_stock -= quantity

    return expected_stock
