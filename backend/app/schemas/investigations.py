from pydantic import BaseModel, Field

ALLOWED_INVESTIGATION_STATUSES = {"IN_PROGRESS", "RESOLVED", "CLOSED"}


class InvestigationCreateRequest(BaseModel):
    alert_id: int = Field(gt=0)
    assigned_to: str | None = Field(default=None, max_length=100)


class InvestigationUpdateRequest(BaseModel):
    findings: str = Field(min_length=1, max_length=8000)
    resolution: str = Field(min_length=1, max_length=100)
    status: str
    performed_by: str | None = Field(default=None, max_length=100)
    assigned_to: str | None = Field(default=None, max_length=100)


class InvestigationResponse(BaseModel):
    id: int
    investigation_id: int | None = None
    investigation_code: str
    alert_id: int
    alert_code: str | None = None
    assigned_to: str | None = None
    status: str
    findings: str | None = None
    resolution: str | None = None
    started_at: str | None = None
    closed_at: str | None = None
    created_at: str | None = None
    message: str | None = None


class InvestigationEventResponse(BaseModel):
    id: int
    event_id: int
    event_type: str
    description: str
    performed_by: str | None = None
    event_at: str | None = None
