from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import BACKEND_ROOT
from app.models import (
    CycleCount,
    InventoryMovement,
    Investigation,
    SKU,
    ShrinkageAlert,
    Store,
)

METRICS_JSON = BACKEND_ROOT / "data" / "generated" / "model_metrics.json"
METRICS_CSV = BACKEND_ROOT / "data" / "generated" / "model_metrics.csv"


def dashboard_summary(db: Session) -> dict:
    return {
        "stores": db.query(func.count(Store.id)).scalar() or 0,
        "skus": db.query(func.count(SKU.id)).scalar() or 0,
        "inventory_movements": db.query(func.count(InventoryMovement.id)).scalar() or 0,
        "cycle_counts": db.query(func.count(CycleCount.id)).scalar() or 0,
        "alerts_total": db.query(func.count(ShrinkageAlert.id)).scalar() or 0,
        "alerts_open": (
            db.query(func.count(ShrinkageAlert.id))
            .filter(ShrinkageAlert.status == "OPEN")
            .scalar()
            or 0
        ),
        "alerts_critical": (
            db.query(func.count(ShrinkageAlert.id))
            .filter(ShrinkageAlert.severity == "HIGH")
            .scalar()
            or 0
        ),
        "investigations_in_progress": (
            db.query(func.count(Investigation.id))
            .filter(Investigation.status == "IN_PROGRESS")
            .scalar()
            or 0
        ),
        "investigations_resolved": (
            db.query(func.count(Investigation.id))
            .filter(Investigation.status == "RESOLVED")
            .scalar()
            or 0
        ),
    }


def analytics_summary(db: Session) -> dict:
    severity_rows = (
        db.query(ShrinkageAlert.severity, func.count(ShrinkageAlert.id))
        .group_by(ShrinkageAlert.severity)
        .all()
    )
    status_rows = (
        db.query(ShrinkageAlert.status, func.count(ShrinkageAlert.id))
        .group_by(ShrinkageAlert.status)
        .all()
    )
    investigation_rows = (
        db.query(Investigation.status, func.count(Investigation.id))
        .group_by(Investigation.status)
        .all()
    )
    store_rows = (
        db.query(
            ShrinkageAlert.store_id,
            Store.store_code,
            Store.name,
            func.count(ShrinkageAlert.id),
        )
        .join(Store, Store.id == ShrinkageAlert.store_id)
        .group_by(ShrinkageAlert.store_id, Store.store_code, Store.name)
        .order_by(func.count(ShrinkageAlert.id).desc())
        .limit(10)
        .all()
    )
    trend_rows = (
        db.query(
            func.date(ShrinkageAlert.detected_at).label("day"),
            func.count(ShrinkageAlert.id),
        )
        .group_by(func.date(ShrinkageAlert.detected_at))
        .order_by(func.date(ShrinkageAlert.detected_at))
        .all()
    )

    return {
        "alerts_by_severity": [
            {"name": name or "UNKNOWN", "value": int(count)} for name, count in severity_rows
        ],
        "alerts_by_status": [
            {"name": name or "UNKNOWN", "value": int(count)} for name, count in status_rows
        ],
        "investigations_by_status": [
            {"name": name or "UNKNOWN", "value": int(count)} for name, count in investigation_rows
        ],
        "alerts_by_store": [
            {
                "store_id": store_id,
                "store_code": store_code,
                "name": store_name,
                "value": int(count),
            }
            for store_id, store_code, store_name, count in store_rows
        ],
        "alerts_over_time": [
            {"date": str(day), "value": int(count)} for day, count in trend_rows
        ],
    }


def model_metrics() -> dict:
    import json
    import csv

    if METRICS_JSON.exists():
        return json.loads(METRICS_JSON.read_text(encoding="utf-8"))

    if METRICS_CSV.exists():
        with METRICS_CSV.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        return {
            "source": str(METRICS_CSV),
            "synthetic_data": True,
            "disclaimer": (
                "These metrics were produced on synthetic cycle counts. "
                "They are not real-world production accuracy."
            ),
            "models": rows,
        }

    return {
        "source": None,
        "synthetic_data": True,
        "disclaimer": "No model_metrics file found. Run the detection script to generate metrics.",
        "models": [],
    }
