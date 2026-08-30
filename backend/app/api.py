from datetime import datetime
from pathlib import Path
from typing import Any

import redis
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine, get_db
from app.models import CalculatorResult, ClientCase, Document, FactFindSnapshot, JobTrace
from app.schemas import (
    ApplyPreviewRequest,
    CalculatorResultOut,
    CaseCreate,
    CaseOut,
    DocumentOut,
    FactFindOut,
    JobTraceOut,
    LoginRequest,
    LoginResponse,
    QueuedJobResponse,
)

router = APIRouter(prefix="/api/v1")


def _case_or_404(db: Session, case_id: int) -> ClientCase:
    case = db.get(ClientCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "Case not found."})
    return case


def _document_or_404(db: Session, case_id: int, document_id: int) -> Document:
    doc = db.get(Document, document_id)
    if doc is None or doc.case_id != case_id:
        raise HTTPException(status_code=404, detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."})
    return doc


def _queue_task(task, document_id: int, stage: str, db: Session) -> QueuedJobResponse:
    db.add(JobTrace(document_id=document_id, stage=stage, status="queued", message=f"{stage} job queued.", retryable=True))
    db.commit()
    try:
        result = task.delay(document_id)
    except Exception as exc:
        db.add(JobTrace(
            document_id=document_id,
            stage=stage,
            status="failed",
            retryable=True,
            error_code="QUEUE_UNAVAILABLE",
            message="Could not queue background job.",
            log_summary=str(exc),
        ))
        db.commit()
        raise HTTPException(status_code=503, detail={
            "code": "QUEUE_UNAVAILABLE",
            "message": "Could not queue background job.",
            "stage": stage,
            "retryable": True,
            "details": {"error": str(exc)},
            "next_action": "Check Redis and worker containers, then retry.",
        }) from exc
    return QueuedJobResponse(
        status="queued",
        job_id=str(result.id),
        stage=stage,
        message=f"{stage} job queued.",
        next_action="Watch the document job trace.",
    )


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    role = "admin" if payload.username.startswith("admin") else "broker"
    display_name = "Admin Operator" if role == "admin" else "Demo Broker"
    return LoginResponse(token="demo-token", role=role, display_name=display_name)


@router.get("/system/preflight")
def preflight() -> dict[str, Any]:
    settings = get_settings()
    checks: list[dict[str, Any]] = []
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        checks.append({"name": "database", "status": "ok", "message": "Database connection succeeded."})
    except Exception as exc:
        checks.append({"name": "database", "status": "failed", "message": str(exc)})
    try:
        redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1).ping()
        checks.append({"name": "redis", "status": "ok", "message": "Redis ping succeeded."})
    except Exception as exc:
        checks.append({"name": "redis", "status": "failed", "message": str(exc)})
    if settings.ocr_provider and settings.ocr_api_key:
        checks.append({"name": "ocr_provider", "status": "ok", "message": f"OCR provider configured: {settings.ocr_provider}."})
    else:
        checks.append({"name": "ocr_provider", "status": "missing", "message": "Set OCR_PROVIDER and OCR_API_KEY."})
    if settings.llm_provider and settings.llm_api_key:
        checks.append({"name": "llm_provider", "status": "ok", "message": f"LLM provider configured: {settings.llm_provider}."})
    else:
        checks.append({"name": "llm_provider", "status": "missing", "message": "Set LLM_PROVIDER and LLM_API_KEY."})
    blocked = any(check["status"] != "ok" for check in checks)
    return {
        "status": "blocked" if blocked else "ready",
        "checks": checks,
        "next_action": "Fix failed or missing checks, then restart backend and worker." if blocked else "System is ready for real processing.",
    }


@router.get("/cases", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db)) -> list[ClientCase]:
    return list(db.scalars(select(ClientCase).order_by(desc(ClientCase.updated_at))).all())


@router.post("/cases", response_model=CaseOut)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> ClientCase:
    now = datetime.utcnow()
    case = ClientCase(name=payload.name, notes=payload.notes, status="active", created_at=now, updated_at=now)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/cases/{case_id}", response_model=CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db)) -> ClientCase:
    return _case_or_404(db, case_id)


@router.get("/cases/{case_id}/documents", response_model=list[DocumentOut])
def list_documents(case_id: int, db: Session = Depends(get_db)) -> list[Document]:
    _case_or_404(db, case_id)
    return list(db.scalars(select(Document).where(Document.case_id == case_id).order_by(desc(Document.created_at))).all())


@router.post("/cases/{case_id}/documents/upload", response_model=DocumentOut)
def upload_document(case_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)) -> Document:
    _case_or_404(db, case_id)
    settings = get_settings()
    upload_dir = Path(settings.storage_root) / "cases" / str(case_id) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload.bin").name
    storage_path = upload_dir / safe_name
    with storage_path.open("wb") as out:
        out.write(file.file.read())
    now = datetime.utcnow()
    doc = Document(case_id=case_id, original_filename=safe_name, storage_path=str(storage_path), status="uploaded", created_at=now, updated_at=now)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.add(JobTrace(document_id=doc.id, stage="upload", status="succeeded", message="Document uploaded."))
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/cases/{case_id}/documents/{document_id}/process-ocr", response_model=QueuedJobResponse)
def process_ocr(case_id: int, document_id: int, db: Session = Depends(get_db)) -> QueuedJobResponse:
    from app.tasks import process_ocr_task
    _document_or_404(db, case_id, document_id)
    return _queue_task(process_ocr_task, document_id, "ocr_processing", db)


@router.post("/cases/{case_id}/documents/{document_id}/build-evidence", response_model=QueuedJobResponse)
def build_evidence(case_id: int, document_id: int, db: Session = Depends(get_db)) -> QueuedJobResponse:
    from app.tasks import build_evidence_task
    _document_or_404(db, case_id, document_id)
    return _queue_task(build_evidence_task, document_id, "evidence_building", db)


@router.post("/cases/{case_id}/documents/{document_id}/map-fact-find", response_model=QueuedJobResponse)
def map_fact_find(case_id: int, document_id: int, db: Session = Depends(get_db)) -> QueuedJobResponse:
    from app.tasks import map_fact_find_task
    _document_or_404(db, case_id, document_id)
    return _queue_task(map_fact_find_task, document_id, "fact_find_mapping", db)


@router.get("/cases/{case_id}/documents/{document_id}/jobs", response_model=list[JobTraceOut])
def document_jobs(case_id: int, document_id: int, db: Session = Depends(get_db)) -> list[JobTrace]:
    _document_or_404(db, case_id, document_id)
    return list(db.scalars(select(JobTrace).where(JobTrace.document_id == document_id).order_by(JobTrace.created_at)).all())


@router.get("/cases/{case_id}/fact-find/current", response_model=FactFindOut)
def current_fact_find(case_id: int, db: Session = Depends(get_db)) -> FactFindSnapshot:
    _case_or_404(db, case_id)
    snapshot = db.scalars(select(FactFindSnapshot).where(FactFindSnapshot.case_id == case_id, FactFindSnapshot.is_current.is_(True))).first()
    if snapshot is None:
        snapshot = FactFindSnapshot(case_id=case_id, version=1, is_current=True, form_data={"applicants": {}, "income": {}, "expenses": {}, "assets": {}, "liabilities": {}})
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
    return snapshot


@router.post("/cases/{case_id}/fact-find/apply-preview", response_model=FactFindOut)
def apply_fact_find_preview(case_id: int, payload: ApplyPreviewRequest, db: Session = Depends(get_db)) -> FactFindSnapshot:
    _case_or_404(db, case_id)
    current = db.scalars(select(FactFindSnapshot).where(FactFindSnapshot.case_id == case_id, FactFindSnapshot.is_current.is_(True))).first()
    current_data = current.form_data if current else {}
    current_version = current.version if current else 0
    if current:
        current.is_current = False
    merged = {**current_data, **payload.changes}
    snapshot = FactFindSnapshot(case_id=case_id, version=current_version + 1, is_current=True, form_data=merged)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.post("/cases/{case_id}/calculator/auto-populate")
def calculator_auto_populate(case_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    _case_or_404(db, case_id)
    fact_find = current_fact_find(case_id, db)
    return {
        "status": "ready",
        "case_id": case_id,
        "source_version": fact_find.version,
        "adapters": {
            "BOCAL": {"summary": "Maps investment debt into negative gearing when purpose is investment.", "warnings": []},
            "Brighten": {"summary": "Treats equivalent investment debt as commitments where negative gearing treatment is unsupported.", "warnings": ["Negative gearing placement differs from BOCAL; review before submission."]},
        },
    }


@router.post("/cases/{case_id}/calculator/run", response_model=list[CalculatorResultOut])
def run_calculators(case_id: int, db: Session = Depends(get_db)) -> list[CalculatorResult]:
    _case_or_404(db, case_id)
    db.query(CalculatorResult).filter(CalculatorResult.case_id == case_id).delete()
    results = [
        CalculatorResult(case_id=case_id, lender="BOCAL", status="pass", max_borrowing_capacity=842000, monthly_surplus=1840, assessment_rate=9.12, notes={"adapter": "negative_gearing_supported", "explanation": "Investment loan placed in negative gearing fields."}),
        CalculatorResult(case_id=case_id, lender="Brighten", status="pass_with_review", max_borrowing_capacity=788000, monthly_surplus=1260, assessment_rate=9.35, notes={"adapter": "commitment_based", "explanation": "Investment loan treated as commitment; review lender policy."}),
    ]
    db.add_all(results)
    db.commit()
    for result in results:
        db.refresh(result)
    return sorted(results, key=lambda item: item.max_borrowing_capacity, reverse=True)


@router.get("/cases/{case_id}/calculator/results", response_model=list[CalculatorResultOut])
def calculator_results(case_id: int, db: Session = Depends(get_db)) -> list[CalculatorResult]:
    _case_or_404(db, case_id)
    return list(db.scalars(select(CalculatorResult).where(CalculatorResult.case_id == case_id).order_by(desc(CalculatorResult.max_borrowing_capacity))).all())
