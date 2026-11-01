from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class VarianceRequest(BaseModel):
    store_id: int = Field(gt=0)
    sku_id: int = Field(gt=0)
    counted_quantity: Decimal = Field(ge=0)
    as_of: datetime | None = None
    cycle_count_id: int | None = Field(default=None, gt=0)


class ExpectedStockResponse(BaseModel):
    store_id: int
    sku_id: int
    expected_stock: str
    as_of: datetime | None = None
    unit: str = "quantity"


class VarianceResponse(BaseModel):
    store_id: int
    sku_id: int
    expected_quantity: str
    counted_quantity: str
    variance_quantity: str
    variance_type: str
    as_of: datetime | None = None
