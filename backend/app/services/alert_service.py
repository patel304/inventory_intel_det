
from datetime import datetime, timezone
from decimal import Decimal

from app.models import ShrinkageAlert
from app.services.variance_service import calculate_variance


def detect_shrinkage(
    db,
    store_id,
    sku_id,
    counted_quantity,
    threshold=Decimal("5"),
):
    result = calculate_variance(
        db,
        store_id,
        sku_id,
        counted_quantity,
    )

    expected = Decimal(result["expected_quantity"])
    counted = Decimal(result["counted_quantity"])
    variance = Decimal(result["variance_quantity"])

    # Only significant stock shortages create alerts.
    shortage = abs(variance)

    if variance >= 0 or shortage < threshold:
        return {
            "alert_created": False,
            "message": "No significant shrinkage detected",
            **result,
        }

    alert_number = db.query(ShrinkageAlert).count() + 1
    alert_code = (
        f"SHR-{datetime.now(timezone.utc).strftime('%Y')}-"
        f"{alert_number:06d}"
    )

    alert = ShrinkageAlert(
        alert_code=alert_code,
        store_id=store_id,
        sku_id=sku_id,
        detection_rule="CYCLE_COUNT_SHORTAGE",
        severity="HIGH" if shortage >= 20 else "MEDIUM",
        confidence_score=Decimal("0.90"),
        expected_quantity=expected,
        observed_quantity=counted,
        variance_quantity=variance,
        status="OPEN",
        detected_at=datetime.now(timezone.utc),
    )

    db.add(alert)
    db.flush()

    return {
        "alert_created": True,
        "alert_id": alert.id,
        "alert_code": alert.alert_code,
        **result,
    }
def get_all_alerts(db, status=None):
    query = db.query(ShrinkageAlert)

    if status:
        query = query.filter(ShrinkageAlert.status == status.upper())

    alerts = query.order_by(
        ShrinkageAlert.detected_at.desc()
    ).all()

    return [
        {
            "id": alert.id,
            "alert_code": alert.alert_code,
            "store_id": alert.store_id,
            "sku_id": alert.sku_id,
            "severity": alert.severity,
            "status": alert.status,
            "expected_quantity": str(alert.expected_quantity),
            "observed_quantity": str(alert.observed_quantity),
            "variance_quantity": str(alert.variance_quantity),
            "detected_at": alert.detected_at.isoformat()
            if alert.detected_at else None,
        }
        for alert in alerts
    ]