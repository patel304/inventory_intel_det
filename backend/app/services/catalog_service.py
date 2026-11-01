from sqlalchemy.orm import Session

from app.models import CycleCount, SKU, Store
from app.schemas.common import clamp_page
from app.services.inventory_service import calculate_expected_stock


def list_stores(db: Session, search: str | None = None, page: int = 1, page_size: int = 25) -> dict:
    page, page_size = clamp_page(page, page_size)
    query = db.query(Store)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            (Store.store_code.like(like)) | (Store.name.like(like)) | (Store.city.like(like))
        )
    total = query.count()
    rows = (
        query.order_by(Store.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {
                "id": store.id,
                "store_code": store.store_code,
                "name": store.name,
                "city": store.city,
                "state": store.state,
                "is_active": store.is_active,
            }
            for store in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def list_skus(db: Session, search: str | None = None, category: str | None = None, page: int = 1, page_size: int = 25) -> dict:
    page, page_size = clamp_page(page, page_size)
    query = db.query(SKU)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter((SKU.sku_code.like(like)) | (SKU.name.like(like)))
    if category:
        query = query.filter(SKU.category == category)
    total = query.count()
    rows = (
        query.order_by(SKU.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {
                "id": sku.id,
                "sku_code": sku.sku_code,
                "name": sku.name,
                "category": sku.category,
                "unit_cost": str(sku.unit_cost),
                "unit_price": str(sku.unit_price),
                "is_active": sku.is_active,
            }
            for sku in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def list_cycle_counts(
    db: Session,
    store_id: int | None = None,
    sku_id: int | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    page, page_size = clamp_page(page, page_size)
    query = db.query(CycleCount)
    if store_id:
        query = query.filter(CycleCount.store_id == store_id)
    if sku_id:
        query = query.filter(CycleCount.sku_id == sku_id)
    total = query.count()
    rows = (
        query.order_by(CycleCount.counted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "count_code": row.count_code,
                "store_id": row.store_id,
                "sku_id": row.sku_id,
                "counted_quantity": str(row.counted_quantity),
                "counted_at": row.counted_at.isoformat() if row.counted_at else None,
                "count_status": row.count_status,
            }
            for row in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def inventory_lookup(db: Session, store_id: int, sku_id: int) -> dict:
    expected = calculate_expected_stock(db, store_id, sku_id)
    latest_count = (
        db.query(CycleCount)
        .filter(CycleCount.store_id == store_id, CycleCount.sku_id == sku_id)
        .order_by(CycleCount.counted_at.desc())
        .first()
    )
    store = db.query(Store).filter(Store.id == store_id).first()
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    return {
        "store_id": store_id,
        "store_code": store.store_code if store else None,
        "sku_id": sku_id,
        "sku_code": sku.sku_code if sku else None,
        "expected_stock": str(expected),
        "latest_cycle_count": (
            {
                "id": latest_count.id,
                "count_code": latest_count.count_code,
                "counted_quantity": str(latest_count.counted_quantity),
                "counted_at": latest_count.counted_at.isoformat() if latest_count.counted_at else None,
            }
            if latest_count
            else None
        ),
    }
