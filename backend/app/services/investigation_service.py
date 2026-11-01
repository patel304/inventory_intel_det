from datetime import datetime, timezone

from sqlalchemy.orm import Session
from uuid import uuid4

from app.models import Investigation, InvestigationEvent, ShrinkageAlert
from app.schemas.common import clamp_page
from app.schemas.investigations import ALLOWED_INVESTIGATION_STATUSES

ACTIVE_INVESTIGATION_STATUSES = {"IN_PROGRESS"}
ALERT_STATUS_FOR_INVESTIGATION = {
    "IN_PROGRESS": "INVESTIGATING",
    "RESOLVED": "RESOLVED",
    "CLOSED": "CLOSED",
}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def serialize_investigation(
    investigation: Investigation,
    alert: ShrinkageAlert | None = None,
    message: str | None = None,
) -> dict:
    payload = {
        "id": investigation.id,
        "investigation_id": investigation.id,
        "investigation_code": investigation.investigation_code,
        "alert_id": investigation.alert_id,
        "alert_code": alert.alert_code if alert else None,
        "assigned_to": investigation.assigned_to,
        "status": investigation.status,
        "findings": investigation.findings,
        "resolution": investigation.resolution,
        "started_at": _iso(investigation.started_at),
        "closed_at": _iso(investigation.closed_at),
        "created_at": _iso(investigation.created_at),
    }
    if message:
        payload["message"] = message
    return payload


def _add_event(db: Session, investigation_id: int, event_type: str, description: str, performed_by: str | None):
    event = InvestigationEvent(
        investigation_id=investigation_id,
        event_type=event_type,
        description=description,
        performed_by=performed_by,
        event_at=_now(),
    )
    db.add(event)
    return event


def create_investigation(db: Session, alert_id: int, assigned_to: str | None = None):
    alert = db.query(ShrinkageAlert).filter(ShrinkageAlert.id == alert_id).first()
    if not alert:
        return None

    existing = (
        db.query(Investigation)
        .filter(
            Investigation.alert_id == alert_id,
            Investigation.status.in_(ACTIVE_INVESTIGATION_STATUSES),
        )
        .first()
    )
    if existing:
        raise ValueError("An in-progress investigation already exists for this alert")

    investigation = Investigation(
        investigation_code=f"INV-{_now().year}-{uuid4().hex[:8].upper()}",
        alert_id=alert_id,
        assigned_to=assigned_to,
        status="IN_PROGRESS",
        started_at=_now(),
    )
    db.add(investigation)
    db.flush()

    assigned_note = f" Assigned to {assigned_to}." if assigned_to else ""
    _add_event(
        db,
        investigation.id,
        "INVESTIGATION_STARTED",
        f"Investigation started for alert {alert.alert_code}.{assigned_note}",
        assigned_to,
    )

    alert.status = "INVESTIGATING"
    db.flush()
    return serialize_investigation(
        investigation, alert, message="Investigation created successfully"
    )


def update_investigation(
    db: Session,
    investigation_id: int,
    findings: str,
    resolution: str,
    status: str,
    performed_by: str | None = None,
    assigned_to: str | None = None,
):
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id)
        .first()
    )
    if not investigation:
        return None

    status = status.upper()
    if status not in ALLOWED_INVESTIGATION_STATUSES:
        raise ValueError("Invalid investigation status")

    if assigned_to is not None:
        investigation.assigned_to = assigned_to

    investigation.findings = findings
    investigation.resolution = resolution
    investigation.status = status

    now = _now()
    if status in {"RESOLVED", "CLOSED"}:
        investigation.closed_at = now
    else:
        investigation.closed_at = None

    alert = (
        db.query(ShrinkageAlert)
        .filter(ShrinkageAlert.id == investigation.alert_id)
        .first()
    )
    if alert:
        alert.status = ALERT_STATUS_FOR_INVESTIGATION[status]

    _add_event(
        db,
        investigation.id,
        "INVESTIGATION_UPDATED",
        (
            f"Status: {status}. "
            f"Findings: {findings}. "
            f"Resolution: {resolution}"
        ),
        performed_by,
    )
    db.flush()
    return serialize_investigation(
        investigation, alert, message="Investigation updated successfully"
    )


def list_investigations(
    db: Session,
    status: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    page, page_size = clamp_page(page, page_size)
    query = db.query(Investigation)
    if status:
        query = query.filter(Investigation.status == status.upper())

    total = query.count()
    rows = (
        query.order_by(Investigation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    alert_ids = {row.alert_id for row in rows}
    alerts = {
        alert.id: alert
        for alert in db.query(ShrinkageAlert).filter(ShrinkageAlert.id.in_(alert_ids)).all()
    } if alert_ids else {}

    return {
        "items": [serialize_investigation(row, alerts.get(row.alert_id)) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def get_investigation(db: Session, investigation_id: int) -> dict | None:
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id)
        .first()
    )
    if not investigation:
        return None
    alert = (
        db.query(ShrinkageAlert)
        .filter(ShrinkageAlert.id == investigation.alert_id)
        .first()
    )
    return serialize_investigation(investigation, alert)


def get_investigation_events(db: Session, investigation_id: int):
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id)
        .first()
    )
    if not investigation:
        return None

    events = (
        db.query(InvestigationEvent)
        .filter(InvestigationEvent.investigation_id == investigation_id)
        .order_by(InvestigationEvent.event_at.asc())
        .all()
    )
    return [
        {
            "id": event.id,
            "event_id": event.id,
            "event_type": event.event_type,
            "description": event.description,
            "performed_by": event.performed_by,
            "event_at": _iso(event.event_at),
        }
        for event in events
    ]
