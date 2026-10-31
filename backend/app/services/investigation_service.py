
from datetime import datetime, timezone
from uuid import uuid4

from app.models import (
    ShrinkageAlert,
    Investigation,
    InvestigationEvent,
)


def create_investigation(db, alert_id, assigned_to=None):
    alert = (
        db.query(ShrinkageAlert)
        .filter(ShrinkageAlert.id == alert_id)
        .first()
    )

    if not alert:
        return None

    investigation = Investigation(
    investigation_code=(
        f"INV-{datetime.now(timezone.utc).year}-"
        f"{uuid4().hex[:8].upper()}"
    ),
    alert_id=alert_id,
    assigned_to=assigned_to,
    status="IN_PROGRESS",
    started_at=datetime.now(timezone.utc),
)

    db.add(investigation)
    db.flush()

    event = InvestigationEvent(
        investigation_id=investigation.id,
        event_type="INVESTIGATION_STARTED",
        description=f"Investigation started for alert {alert.alert_code}",
        performed_by=assigned_to,
        event_at=datetime.now(timezone.utc),
    )

    alert.status = "INVESTIGATING"

    db.add(event)
    db.flush()

    return {
        "investigation_id": investigation.id,
        "alert_id": alert_id,
        "alert_code": alert.alert_code,
        "status": investigation.status,
        "message": "Investigation created successfully",
    }
    

from datetime import datetime, timezone

def update_investigation(
    db,
    investigation_id,
    findings,
    resolution,
    status,
    performed_by=None,
):
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id)
        .first()
    )

    if not investigation:
        return None

    allowed_statuses = {"IN_PROGRESS", "RESOLVED", "CLOSED"}

    if status not in allowed_statuses:
        raise ValueError("Invalid investigation status")

    now = datetime.now(timezone.utc)

    investigation.findings = findings
    investigation.resolution = resolution
    investigation.status = status

    if status in {"RESOLVED", "CLOSED"}:
        investigation.closed_at = now

    event = InvestigationEvent(
        investigation_id=investigation.id,
        event_type="INVESTIGATION_UPDATED",
        description=(
            f"Status: {status}. "
            f"Findings: {findings}. "
            f"Resolution: {resolution}"
        ),
        performed_by=performed_by,
        event_at=now,
    )

    db.add(event)
    db.flush()

    return {
        "investigation_id": investigation.id,
        "status": investigation.status,
        "findings": investigation.findings,
        "resolution": investigation.resolution,
        "message": "Investigation updated successfully",
    }


def get_investigation_events(db, investigation_id):
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id)
        .first()
    )

    if not investigation:
        return None

    events = (
        db.query(InvestigationEvent)
        .filter(
            InvestigationEvent.investigation_id == investigation_id
        )
        .order_by(InvestigationEvent.event_at.asc())
        .all()
    )

    return [
        {
            "event_id": event.id,
            "event_type": event.event_type,
            "description": event.description,
            "performed_by": event.performed_by,
            "event_at": (
                event.event_at.isoformat()
                if event.event_at else None
            ),
        }
        for event in events
    ]

