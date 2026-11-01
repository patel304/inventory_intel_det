from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stats_service import analytics_summary, dashboard_summary, model_metrics

router = APIRouter(tags=["analytics"])


@router.get("/dashboard/summary")
def dashboard(db: Session = Depends(get_db)):
    return dashboard_summary(db)


@router.get("/analytics/summary")
def analytics(db: Session = Depends(get_db)):
    return analytics_summary(db)


@router.get("/metrics/model")
def metrics():
    return model_metrics()
