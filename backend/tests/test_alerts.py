from decimal import Decimal

from app.models import ShrinkageAlert
from app.services.alert_service import detect_shrinkage


def test_detect_creates_alert_for_shortage(db, seeded):
    result = detect_shrinkage(
        db,
        seeded["store_a"].id,
        seeded["sku"].id,
        counted_quantity=Decimal("40"),
        threshold=Decimal("5"),
        as_of=seeded["t0"],
    )
    # as_of opening day: expected 100, counted 40, shortage 60
    assert result["alert_created"] is True
    assert db.query(ShrinkageAlert).count() == 1


def test_detect_skips_duplicate_open_alert(db, seeded):
    detect_shrinkage(
        db,
        seeded["store_a"].id,
        seeded["sku"].id,
        counted_quantity=Decimal("40"),
        as_of=seeded["t0"],
    )
    second = detect_shrinkage(
        db,
        seeded["store_a"].id,
        seeded["sku"].id,
        counted_quantity=Decimal("30"),
        as_of=seeded["t0"],
    )
    assert second["alert_created"] is False
    assert db.query(ShrinkageAlert).count() == 1


def test_detect_no_alert_when_matched(db, seeded):
    result = detect_shrinkage(
        db,
        seeded["store_a"].id,
        seeded["sku"].id,
        counted_quantity=Decimal("100"),
        as_of=seeded["t0"],
    )
    assert result["alert_created"] is False
    assert db.query(ShrinkageAlert).count() == 0


def test_alert_serialization_includes_detection_metadata_and_estimated_loss(db, seeded):
    from app.services.alert_service import get_alert

    result = detect_shrinkage(
        db,
        seeded["store_a"].id,
        seeded["sku"].id,
        counted_quantity=Decimal("40"),
        threshold=Decimal("5"),
        as_of=seeded["t0"],
    )

    alert = get_alert(db, result["alert_id"])

    assert alert["detection_rule"] == "CYCLE_COUNT_SHORTAGE"
    assert Decimal(alert["confidence_score"]) == Decimal("0.90")
    assert alert["variance_quantity"] == "-60.000"
    assert alert["estimated_loss"] == "600.00"
