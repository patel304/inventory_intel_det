from decimal import Decimal

from app.models import InvestigationEvent, ShrinkageAlert
from app.services.alert_service import detect_shrinkage
from app.services.investigation_service import (
    create_investigation,
    get_investigation_events,
    update_investigation,
)


def _open_alert(db, seeded):
    result = detect_shrinkage(
        db,
        seeded["store_a"].id,
        seeded["sku"].id,
        counted_quantity=Decimal("40"),
        as_of=seeded["t0"],
    )
    return result["alert_id"]


def test_create_investigation_and_events(db, seeded):
    alert_id = _open_alert(db, seeded)
    created = create_investigation(db, alert_id, assigned_to="Ada")
    assert created["status"] == "IN_PROGRESS"
    alert = db.query(ShrinkageAlert).filter(ShrinkageAlert.id == alert_id).first()
    assert alert.status == "INVESTIGATING"
    events = get_investigation_events(db, created["investigation_id"])
    assert events[0]["event_type"] == "INVESTIGATION_STARTED"


def test_duplicate_investigation_rejected(db, seeded):
    alert_id = _open_alert(db, seeded)
    create_investigation(db, alert_id, assigned_to="Ada")
    try:
        create_investigation(db, alert_id, assigned_to="Bob")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_update_investigation_syncs_alert_and_history(db, seeded):
    alert_id = _open_alert(db, seeded)
    created = create_investigation(db, alert_id, assigned_to="Ada")
    updated = update_investigation(
        db,
        created["investigation_id"],
        findings="Theft suspected at receiving dock",
        resolution="Camera review completed",
        status="RESOLVED",
        performed_by="Ada",
    )
    assert updated["status"] == "RESOLVED"
    alert = db.query(ShrinkageAlert).filter(ShrinkageAlert.id == alert_id).first()
    assert alert.status == "RESOLVED"
    events = get_investigation_events(db, created["investigation_id"])
    assert len(events) == 2
    assert db.query(InvestigationEvent).count() == 2
