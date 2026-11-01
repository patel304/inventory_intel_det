from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import CycleCount, SKU, ShrinkageAlert, Store
from app.schemas.common import clamp_page
from app.services.variance_service import calculate_variance

OPEN_ALERT_STATUSES = {"OPEN", "INVESTIGATING"}


def _iso(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def serialize_alert(alert: ShrinkageAlert, store: Store | None = None, sku: SKU | None = None) -> dict:
    variance = alert.variance_quantity
    store = store or getattr(alert, "store", None)
    sku = sku or getattr(alert, "sku", None)
    return {
        "id": alert.id,
        "alert_code": alert.alert_code,
        "store_id": alert.store_id,
        "store_code": store.store_code if store else None,
        "store_name": store.name if store else None,
        "sku_id": alert.sku_id,
        "sku_code": sku.sku_code if sku else None,
        "sku_name": sku.name if sku else None,
        "cycle_count_id": alert.cycle_count_id,
        "detection_rule": alert.detection_rule,
        "severity": alert.severity,
        "status": alert.status,
        "confidence_score": (
            str(alert.confidence_score) if alert.confidence_score is not None else None
        ),
        "expected_quantity": (
            str(alert.expected_quantity) if alert.expected_quantity is not None else None
        ),
        "observed_quantity": (
            str(alert.observed_quantity) if alert.observed_quantity is not None else None
        ),
        "variance_quantity": str(variance) if variance is not None else None,
        "variance": str(variance) if variance is not None else None,
        "unit_cost": str(sku.unit_cost) if sku and sku.unit_cost is not None else None,
        "estimated_loss": (
            str((abs(Decimal(variance)) * Decimal(sku.unit_cost)).quantize(Decimal("0.01")))
            if variance is not None and Decimal(variance) < 0 and sku and sku.unit_cost is not None
            else "0.00" if variance is not None and Decimal(variance) >= 0 else None
        ),
        "detected_at": _iso(alert.detected_at),
    }


def _severity_for_shortage(shortage: Decimal) -> str:
    if shortage >= 20:
        return "HIGH"
    if shortage >= 10:
        return "MEDIUM"
    return "LOW"


def detect_shrinkage(
    db: Session,
    store_id: int,
    sku_id: int,
    counted_quantity,
    threshold: Decimal = Decimal("5"),
    cycle_count_id: int | None = None,
    as_of: datetime | None = None,
) -> dict:
    if cycle_count_id is not None:
        cycle_count = (
            db.query(CycleCount)
            .filter(
                CycleCount.id == cycle_count_id,
                CycleCount.store_id == store_id,
                CycleCount.sku_id == sku_id,
            )
            .first()
        )
        if cycle_count is None:
            raise ValueError("Cycle count not found for this store and SKU")
        as_of = cycle_count.counted_at

    result = calculate_variance(
        db,
        store_id,
        sku_id,
        counted_quantity,
        as_of=as_of,
    )

    expected = Decimal(result["expected_quantity"])
    counted = Decimal(result["counted_quantity"])
    variance = Decimal(result["variance_quantity"])
    shortage = abs(variance) if variance < 0 else Decimal("0")

    if variance >= 0 or shortage < threshold:
        return {
            "alert_created": False,
            "message": "No significant shrinkage detected",
            **result,
        }

    existing = (
        db.query(ShrinkageAlert)
        .filter(
            ShrinkageAlert.store_id == store_id,
            ShrinkageAlert.sku_id == sku_id,
            ShrinkageAlert.status.in_(OPEN_ALERT_STATUSES),
        )
    )
    if cycle_count_id is not None:
        existing = existing.filter(ShrinkageAlert.cycle_count_id == cycle_count_id)
    existing_alert = existing.order_by(ShrinkageAlert.detected_at.desc()).first()
    if existing_alert:
        return {
            "alert_created": False,
            "message": "An open alert already exists for this store and SKU",
            "alert_id": existing_alert.id,
            "alert_code": existing_alert.alert_code,
            **result,
        }

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    alert_code = f"SHR-{now.year}-{uuid4().hex[:8].upper()}"

    alert = ShrinkageAlert(
        alert_code=alert_code,
        store_id=store_id,
        sku_id=sku_id,
        cycle_count_id=cycle_count_id,
        detection_rule="CYCLE_COUNT_SHORTAGE",
        severity=_severity_for_shortage(shortage),
        confidence_score=Decimal("0.90"),
        expected_quantity=expected,
        observed_quantity=counted,
        variance_quantity=variance,
        status="OPEN",
        detected_at=now,
    )
    db.add(alert)
    db.flush()

    return {
        "alert_created": True,
        "message": "Shrinkage alert created",
        "alert_id": alert.id,
        "alert_code": alert.alert_code,
        **result,
    }


def get_all_alerts(
    db: Session,
    status: str | None = None,
    severity: str | None = None,
    store_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    page, page_size = clamp_page(page, page_size)
    query = db.query(ShrinkageAlert).outerjoin(Store).outerjoin(SKU)

    if status:
        query = query.filter(ShrinkageAlert.status == status.upper())
    if severity:
        query = query.filter(ShrinkageAlert.severity == severity.upper())
    if store_id:
        query = query.filter(ShrinkageAlert.store_id == store_id)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            (ShrinkageAlert.alert_code.like(like))
            | (Store.store_code.like(like))
            | (SKU.sku_code.like(like))
        )

    total = query.count()
    alerts = (
        query.order_by(ShrinkageAlert.detected_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    store_ids = {alert.store_id for alert in alerts}
    sku_ids = {alert.sku_id for alert in alerts}
    stores = {
        store.id: store
        for store in db.query(Store).filter(Store.id.in_(store_ids)).all()
    } if store_ids else {}
    skus = {
        sku.id: sku
        for sku in db.query(SKU).filter(SKU.id.in_(sku_ids)).all()
    } if sku_ids else {}

    return {
        "items": [
            serialize_alert(alert, stores.get(alert.store_id), skus.get(alert.sku_id))
            for alert in alerts
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def get_alert(db: Session, alert_id: int) -> dict | None:
    alert = db.query(ShrinkageAlert).filter(ShrinkageAlert.id == alert_id).first()
    if not alert:
        return None
    store = db.query(Store).filter(Store.id == alert.store_id).first()
    sku = db.query(SKU).filter(SKU.id == alert.sku_id).first()
    return serialize_alert(alert, store, sku)
