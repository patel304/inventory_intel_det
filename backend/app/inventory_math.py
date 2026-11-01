from decimal import Decimal

INCREASE_TYPES = {
    "OPENING_BALANCE",
    "RECEIPT",
    "RETURN_IN",
    "TRANSFER_IN",
    "ADJUSTMENT_IN",
}

DECREASE_TYPES = {
    "SALE",
    "DAMAGE",
    "TRANSFER_OUT",
    "ADJUSTMENT_OUT",
}

KNOWN_MOVEMENT_TYPES = INCREASE_TYPES | DECREASE_TYPES


def signed_quantity(movement_type: str, quantity) -> Decimal:
    """Apply the inventory equation to a positive movement magnitude."""
    amount = Decimal(str(quantity or 0))
    if movement_type in INCREASE_TYPES:
        return amount
    if movement_type in DECREASE_TYPES:
        return -amount
    return Decimal("0")
