from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.investigations import (
    InvestigationCreateRequest,
    InvestigationUpdateRequest,
)
from app.services.investigation_service import (
    create_investigation,
    get_investigation,
    get_investigation_events,
    list_investigations,
    update_investigation,
)

router = APIRouter(tags=["investigations"])


@router.get("/investigations")
def investigations_list(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_investigations(db, status=status, page=page, page_size=page_size)


@router.get("/investigations/{investigation_id}")
def investigation_detail(investigation_id: int, db: Session = Depends(get_db)):
    result = get_investigation(db, investigation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return result


@router.post("/investigations")
def start_investigation(request: InvestigationCreateRequest, db: Session = Depends(get_db)):
    try:
        result = create_investigation(
            db=db,
            alert_id=request.alert_id,
            assigned_to=request.assigned_to,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        db.commit()
        return result
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(error)) from error
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.put("/investigations/{investigation_id}")
def update_investigation_api(
    investigation_id: int,
    request: InvestigationUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        result = update_investigation(
            db=db,
            investigation_id=investigation_id,
            findings=request.findings,
            resolution=request.resolution,
            status=request.status.upper(),
            performed_by=request.performed_by,
            assigned_to=request.assigned_to,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Investigation not found")
        db.commit()
        return result
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(error)) from error
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get("/investigations/{investigation_id}/events")
def investigation_events_api(investigation_id: int, db: Session = Depends(get_db)):
    result = get_investigation_events(db, investigation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {"items": result, "events": result}
