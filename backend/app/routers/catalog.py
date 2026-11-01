from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.catalog_service import list_skus, list_stores

router = APIRouter(tags=["catalog"])


@router.get("/stores")
def stores(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_stores(db, search=search, page=page, page_size=page_size)


@router.get("/skus")
def skus(
    search: str | None = None,
    category: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_skus(db, search=search, category=category, page=page, page_size=page_size)
