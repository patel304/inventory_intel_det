
from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.inventory_service import calculate_expected_stock
from app.models import Store, SKU
from pydantic import BaseModel, Field
from app.services.variance_service import calculate_variance
from decimal import Decimal
from app.services.alert_service import detect_shrinkage
from typing import Optional
from app.services.alert_service import get_all_alerts
from pydantic import BaseModel
from typing import Optional

from app.services.investigation_service import create_investigation

from app.services.investigation_service import (
    create_investigation,
    update_investigation,
    get_investigation_events,
)

from fastapi.middleware.cors import CORSMiddleware

from app.models import Store, SKU, Investigation

app = FastAPI(
    title="Inventory Shrinkage Detection API",
    description="Backend API for retail inventory monitoring and shrinkage detection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Inventory Shrinkage Detection API is running!"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "inventory-backend"
    }
    
@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "database": "inventory_detection"
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error)
        }
        
@app.get("/inventory/expected-stock/{store_id}/{sku_id}")
def get_expected_stock(
    store_id: int,
    sku_id: int,
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    sku = db.query(SKU).filter(SKU.id == sku_id).first()

    if not store or not sku:
        raise HTTPException(
            status_code=404,
            detail="Store or SKU not found"
        )

    expected_stock = calculate_expected_stock(
        db,
        store_id,
        sku_id
    )

    return {
        "store_id": store_id,
        "sku_id": sku_id,
        "expected_stock": str(expected_stock),
        "unit": "quantity"
    }
class VarianceRequest(BaseModel):
    store_id: int
    sku_id: int
    counted_quantity: Decimal = Field(ge=0)


@app.post("/inventory/variance")
def get_inventory_variance(
    request: VarianceRequest,
    db: Session = Depends(get_db),
):
    if not db.query(Store).filter(Store.id == request.store_id).first():
        raise HTTPException(status_code=404, detail="Store not found")

    if not db.query(SKU).filter(SKU.id == request.sku_id).first():
        raise HTTPException(status_code=404, detail="SKU not found")

    return calculate_variance(
        db,
        request.store_id,
        request.sku_id,
        request.counted_quantity,
    )
    
@app.post("/alerts/detect")
def detect_shrinkage_alert(
    request: VarianceRequest,
    db: Session = Depends(get_db),
):
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
        )
        db.commit()
        return result

    except Exception:
        db.rollback()
        raise
    
@app.get("/alerts")
def list_alerts(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return get_all_alerts(db, status)

class InvestigationRequest(BaseModel):
    alert_id: int
    assigned_to: Optional[str] = None



@app.get("/investigations")
def list_investigations(db: Session = Depends(get_db)):
    investigations = (
        db.query(Investigation)
        .order_by(Investigation.created_at.desc())
        .all()
    )
    return investigations


@app.post("/investigations")
def start_investigation(
    request: InvestigationRequest,
    db: Session = Depends(get_db),
):
    try:
        result = create_investigation(
            db=db,
            alert_id=request.alert_id,
            assigned_to=request.assigned_to,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Alert not found",
            )

        db.commit()
        return result

    except Exception:
        db.rollback()
        raise
    

class InvestigationUpdateRequest(BaseModel):
    findings: str
    resolution: str
    status: str
    performed_by: Optional[str] = None


@app.put("/investigations/{investigation_id}")
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
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Investigation not found",
            )

        db.commit()
        return result

    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        db.rollback()
        raise


@app.get("/investigations/{investigation_id}/events")
def investigation_events_api(
    investigation_id: int,
    db: Session = Depends(get_db),
):
    result = get_investigation_events(db, investigation_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    return result
