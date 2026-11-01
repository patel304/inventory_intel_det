from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SKU, Store
from app.schemas.inventory import ExpectedStockResponse, VarianceRequest
from app.services.catalog_service import inventory_lookup, list_cycle_counts
from app.services.inventory_service import calculate_expected_stock
from app.services.variance_service import calculate_variance

router = APIRouter(tags=["inventory"])


def _require_store_sku(db: Session, store_id: int, sku_id: int) -> None:
    if not db.query(Store).filter(Store.id == store_id).first():
        raise HTTPException(status_code=404, detail="Store not found")
    if not db.query(SKU).filter(SKU.id == sku_id).first():
        raise HTTPException(status_code=404, detail="SKU not found")


@router.get("/inventory/expected-stock/{store_id}/{sku_id}")
def get_expected_stock(
    store_id: int,
    sku_id: int,
    as_of: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    _require_store_sku(db, store_id, sku_id)
    expected_stock = calculate_expected_stock(db, store_id, sku_id, as_of=as_of)
    return ExpectedStockResponse(
        store_id=store_id,
        sku_id=sku_id,
        expected_stock=str(expected_stock),
        as_of=as_of,
    )


@router.post("/inventory/variance")
def get_inventory_variance(request: VarianceRequest, db: Session = Depends(get_db)):
    _require_store_sku(db, request.store_id, request.sku_id)
    return calculate_variance(
        db,
        request.store_id,
        request.sku_id,
        request.counted_quantity,
        as_of=request.as_of,
    )


@router.get("/inventory/lookup")
def get_inventory_lookup(
    store_id: int = Query(gt=0),
    sku_id: int = Query(gt=0),
    db: Session = Depends(get_db),
):
    _require_store_sku(db, store_id, sku_id)
    return inventory_lookup(db, store_id, sku_id)


@router.get("/cycle-counts")
def get_cycle_counts(
    store_id: int | None = None,
    sku_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_cycle_counts(db, store_id=store_id, sku_id=sku_id, page=page, page_size=page_size)
