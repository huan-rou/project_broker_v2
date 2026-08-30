from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    display_name: str


class CaseCreate(BaseModel):
    name: str
    notes: str | None = None


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    original_filename: str
    storage_path: str
    status: str
    document_category: str | None
    ocr_text: str | None
    evidence_json: dict[str, Any] | None
    fact_find_preview: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class JobTraceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    stage: str
    status: str
    retryable: bool
    error_code: str | None
    message: str
    log_summary: str | None
    created_at: datetime


class QueuedJobResponse(BaseModel):
    status: Literal["queued"]
    job_id: str
    stage: str
    message: str
    next_action: str


class FactFindOut(BaseModel):
    id: int
    case_id: int
    version: int
    is_current: bool
    form_data: dict[str, Any]
    created_at: datetime


class ApplyPreviewRequest(BaseModel):
    changes: dict[str, Any]


class CalculatorResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    lender: str
    status: str
    max_borrowing_capacity: int
    monthly_surplus: int
    assessment_rate: float
    notes: dict[str, Any]
    created_at: datetime
