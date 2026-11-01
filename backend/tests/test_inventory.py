from datetime import timedelta
from decimal import Decimal

from app.services.inventory_service import calculate_expected_stock
from app.services.variance_service import calculate_variance


def test_expected_stock_includes_adjustments_and_transfers(db, seeded):
    store_a = seeded["store_a"]
    store_b = seeded["store_b"]
    sku = seeded["sku"]

    # 100 + 20 - 15 - 5 - 10 + 4 + 3 - 2 - 50 = 45 at store A (all movements)
    expected_a = calculate_expected_stock(db, store_a.id, sku.id)
    assert expected_a == Decimal("45")

    # Transfer in only at store B
    expected_b = calculate_expected_stock(db, store_b.id, sku.id)
    assert expected_b == Decimal("10")


def test_historical_stock_excludes_future_sales(db, seeded):
    store_a = seeded["store_a"]
    sku = seeded["sku"]
    as_of = seeded["t0"] + timedelta(days=7, hours=12)
    expected = calculate_expected_stock(db, store_a.id, sku.id, as_of=as_of)
    # Excludes the day-20 sale of 50: 100+20-15-5-10+4+3-2 = 95
    assert expected == Decimal("95")


def test_variance_shortage(db, seeded):
    store_a = seeded["store_a"]
    sku = seeded["sku"]
    as_of = seeded["t0"] + timedelta(days=7, hours=12)
    result = calculate_variance(db, store_a.id, sku.id, counted_quantity=80, as_of=as_of)
    assert result["variance_type"] == "SHORTAGE"
    assert result["expected_quantity"] == "95"
    assert result["variance_quantity"] == "-15"
