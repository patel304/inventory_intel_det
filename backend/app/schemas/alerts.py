from decimal import Decimal

from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    id: int
    alert_code: str
    store_id: int
    store_code: str | None = None
    store_name: str | None = None
    sku_id: int
    sku_code: str | None = None
    sku_name: str | None = None
    cycle_count_id: int | None = None
    detection_rule: str | None = None
    severity: str
    status: str
    confidence_score: str | None = None
    expected_quantity: str | None = None
    observed_quantity: str | None = None
    variance_quantity: str | None = None
    variance: str | None = None
    detected_at: str | None = None


class DetectResponse(BaseModel):
    alert_created: bool
    message: str | None = None
    alert_id: int | None = None
    alert_code: str | None = None
    expected_quantity: str
    counted_quantity: str
    variance_quantity: str
    variance_type: str


class DetectRequest(BaseModel):
    store_id: int = Field(gt=0)
    sku_id: int = Field(gt=0)
    counted_quantity: Decimal = Field(ge=0)
    cycle_count_id: int | None = Field(default=None, gt=0)
    threshold: Decimal = Field(default=Decimal("5"), ge=0)
