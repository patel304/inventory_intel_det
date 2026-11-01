import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import alerts, analytics, catalog, health, inventory, investigations

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("stockguard")

app = FastAPI(
    title="StockGuard Inventory Shrinkage Detection API",
    description="Backend API for retail inventory monitoring and shrinkage detection",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(inventory.router)
app.include_router(alerts.router)
app.include_router(investigations.router)
app.include_router(catalog.router)
app.include_router(analytics.router)
