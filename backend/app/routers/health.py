import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import engine

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/")
def home():
    return {"message": "Inventory Shrinkage Detection API is running!"}


@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "inventory-backend"}


@router.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "connected", "database": "inventory_detection"}
    except Exception:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Database connection failed",
            },
        )
