from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SKU, Store
from app.schemas.inventory import VarianceRequest
from app.services.alert_service import detect_shrinkage, get_alert, get_all_alerts

router = APIRouter(tags=["alerts"])


@router.post("/alerts/detect")
def detect_shrinkage_alert(request: VarianceRequest, db: Session = Depends(get_db)):
    if not db.query(Store).filter(Store.id == request.store_id).first():
        raise HTTPException(status_code=404, detail="Store not found")
    if not db.query(SKU).filter(SKU.id == request.sku_id).first():
        raise HTTPException(status_code=404, detail="SKU not found")

    try:
        result = detect_shrinkage(
            db=db,
            store_id=request.store_id,
            sku_id=request.sku_id,
            counted_quantity=request.counted_quantity,
            cycle_count_id=request.cycle_count_id,
            as_of=request.as_of,
        )
        db.commit()
        return result
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception:
        db.rollback()
        raise


@router.get("/alerts")
def list_alerts(
    status: str | None = None,
    severity: str | None = None,
    store_id: int | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_all_alerts(
        db,
        status=status,
        severity=severity,
        store_id=store_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/alerts/{alert_id}")
def alert_detail(alert_id: int, db: Session = Depends(get_db)):
    result = get_alert(db, alert_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result
