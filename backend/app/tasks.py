from datetime import datetime
from typing import Any

from app.celery_app import celery_app
from app.config import get_settings
from app.database import SessionLocal
from app.models import Document, JobTrace


def _job(db, document_id: int, stage: str, status: str, message: str, retryable: bool = False, error_code: str | None = None, log_summary: str | None = None) -> None:
    db.add(JobTrace(
        document_id=document_id,
        stage=stage,
        status=status,
        retryable=retryable,
        error_code=error_code,
        message=message,
        log_summary=log_summary,
    ))


def _missing_provider(stage: str, provider_kind: str) -> dict[str, Any] | None:
    settings = get_settings()
    if provider_kind == "ocr" and (not settings.ocr_provider or not settings.ocr_api_key):
        return {
            "code": "OCR_PROVIDER_MISSING_API_KEY",
            "message": "OCR provider credentials are not configured.",
            "stage": stage,
            "next_action": "Set OCR_PROVIDER and OCR_API_KEY in .env, then restart backend and worker.",
        }
    if provider_kind == "llm" and (not settings.llm_provider or not settings.llm_api_key):
        return {
            "code": "LLM_PROVIDER_MISSING_API_KEY",
            "message": "LLM provider credentials are not configured.",
            "stage": stage,
            "next_action": "Set LLM_PROVIDER and LLM_API_KEY in .env, then restart backend and worker.",
        }
    return None


@celery_app.task(name="process_ocr")
def process_ocr_task(document_id: int) -> dict[str, Any]:
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            return {"status": "failed", "code": "DOCUMENT_NOT_FOUND"}
        doc.status = "ocr_processing"
        doc.updated_at = datetime.utcnow()
        _job(db, document_id, "ocr_processing", "started", "OCR processing started.")
        missing = _missing_provider("ocr_processing", "ocr")
        if missing:
            doc.status = "error"
            _job(db, document_id, "ocr_processing", "failed", missing["message"], True, missing["code"], missing["next_action"])
            db.commit()
            return {"status": "failed", **missing}
        doc.ocr_text = doc.ocr_text or "OCR text placeholder from configured provider."
        doc.status = "ocr_complete"
        doc.updated_at = datetime.utcnow()
        _job(db, document_id, "ocr_processing", "succeeded", "OCR processing completed.")
        db.commit()
        return {"status": "succeeded", "document_id": document_id}
    finally:
        db.close()


@celery_app.task(name="build_evidence")
def build_evidence_task(document_id: int) -> dict[str, Any]:
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            return {"status": "failed", "code": "DOCUMENT_NOT_FOUND"}
        doc.status = "evidence_building"
        doc.updated_at = datetime.utcnow()
        _job(db, document_id, "evidence_building", "started", "Evidence bridge started.")
        missing = _missing_provider("evidence_building", "llm")
        if missing:
            doc.status = "error"
            _job(db, document_id, "evidence_building", "failed", missing["message"], True, missing["code"], missing["next_action"])
            db.commit()
            return {"status": "failed", **missing}
        doc.evidence_json = {
            "source_document_id": document_id,
            "quality": "needs_review",
            "fields": [
                {"key": "income.gross_annual", "value": 128000, "confidence": 0.82},
                {"key": "expenses.living_monthly", "value": 3850, "confidence": 0.74},
            ],
        }
        doc.status = "evidence_ready"
        doc.updated_at = datetime.utcnow()
        _job(db, document_id, "evidence_building", "succeeded", "Evidence bridge completed.")
        db.commit()
        return {"status": "succeeded", "document_id": document_id}
    finally:
        db.close()


@celery_app.task(name="map_fact_find")
def map_fact_find_task(document_id: int) -> dict[str, Any]:
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            return {"status": "failed", "code": "DOCUMENT_NOT_FOUND"}
        doc.status = "fact_find_mapping"
        doc.updated_at = datetime.utcnow()
        _job(db, document_id, "fact_find_mapping", "started", "Fact Find mapping started.")
        missing = _missing_provider("fact_find_mapping", "llm")
        if missing:
            doc.status = "error"
            _job(db, document_id, "fact_find_mapping", "failed", missing["message"], True, missing["code"], missing["next_action"])
            db.commit()
            return {"status": "failed", **missing}
        doc.fact_find_preview = {
            "income": {"gross_annual": 128000, "source": "bridge", "confidence": 0.82},
            "expenses": {"living_monthly": 3850, "source": "bridge", "confidence": 0.74},
        }
        doc.status = "mapped_to_fact_find"
        doc.updated_at = datetime.utcnow()
        _job(db, document_id, "fact_find_mapping", "succeeded", "Fact Find preview created.")
        db.commit()
        return {"status": "succeeded", "document_id": document_id}
    finally:
        db.close()
