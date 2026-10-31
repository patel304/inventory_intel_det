from decimal import Decimal

from app.services.inventory_service import calculate_expected_stock


def calculate_variance(db, store_id, sku_id, counted_quantity):
    expected = calculate_expected_stock(db, store_id, sku_id)

    counted = Decimal(str(counted_quantity))
    variance = counted - expected

    return {
        "expected_quantity": str(expected),
        "counted_quantity": str(counted),
        "variance_quantity": str(variance),
        "variance_type": (
            "SHORTAGE" if variance < 0
            else "SURPLUS" if variance > 0
            else "MATCHED"
        ),
    }