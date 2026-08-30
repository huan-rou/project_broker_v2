from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import CalculatorResult, ClientCase, Document, FactFindSnapshot, JobTrace, User


def main() -> None:
    db = SessionLocal()
    try:
        broker = db.scalars(select(User).where(User.username == "broker@example.com")).first()
        if broker is None:
            broker = User(username="broker@example.com", display_name="Demo Broker", role="broker")
            db.add(broker)
            db.flush()
        admin = db.scalars(select(User).where(User.username == "admin@example.com")).first()
        if admin is None:
            admin = User(username="admin@example.com", display_name="Admin Operator", role="admin")
            db.add(admin)
            db.flush()
        case = db.scalars(select(ClientCase).where(ClientCase.name == "Nguyen Family Purchase")).first()
        if case is None:
            now = datetime.utcnow()
            case = ClientCase(name="Nguyen Family Purchase", status="active", notes="Seeded thin-slice case: PAYG income, investment loan, and living expense review.", created_by_id=broker.id, created_at=now, updated_at=now)
            db.add(case)
            db.flush()
        if not db.scalars(select(Document).where(Document.case_id == case.id)).first():
            docs = [
                Document(case_id=case.id, original_filename="nguyen_payslip_march.pdf", storage_path="seed://nguyen_payslip_march.pdf", status="mapped_to_fact_find", document_category="payslip", ocr_text="Employer: Southern Robotics Pty Ltd. Gross annualised income: 128000.", evidence_json={"fields": [{"key": "income.gross_annual", "value": 128000, "confidence": 0.82}]}, fact_find_preview={"income": {"gross_annual": 128000, "source": "bridge", "confidence": 0.82}}),
                Document(case_id=case.id, original_filename="everyday_bank_statement.pdf", storage_path="seed://everyday_bank_statement.pdf", status="evidence_ready", document_category="bank_statement", ocr_text="Irregular transaction descriptions normalized to living expense categories.", evidence_json={"fields": [{"key": "expenses.living_monthly", "value": 3850, "confidence": 0.74}]}),
            ]
            db.add_all(docs)
            db.flush()
            for doc in docs:
                db.add(JobTrace(document_id=doc.id, stage="seed", status="succeeded", message="Seeded document workflow state."))
        if not db.scalars(select(FactFindSnapshot).where(FactFindSnapshot.case_id == case.id)).first():
            db.add(FactFindSnapshot(case_id=case.id, version=1, is_current=True, form_data={"applicants": {"primary_name": "Minh Nguyen", "secondary_name": "Linh Nguyen", "dependants": 1}, "income": {"gross_annual": 128000, "source": "OCR Bridge", "confidence": 0.82}, "expenses": {"living_monthly": 3850, "source": "Bank Statement Bridge", "confidence": 0.74}, "assets": {"savings": 142000, "property_value": 620000}, "liabilities": {"investment_loan_balance": 410000, "credit_card_limit": 12000}}))
        if not db.scalars(select(CalculatorResult).where(CalculatorResult.case_id == case.id)).first():
            db.add_all([
                CalculatorResult(case_id=case.id, lender="BOCAL", status="pass", max_borrowing_capacity=842000, monthly_surplus=1840, assessment_rate=9.12, notes={"adapter": "negative_gearing_supported", "explanation": "Investment loan placed in negative gearing fields."}),
                CalculatorResult(case_id=case.id, lender="Brighten", status="pass_with_review", max_borrowing_capacity=788000, monthly_surplus=1260, assessment_rate=9.35, notes={"adapter": "commitment_based", "explanation": "Investment loan treated as commitment; review lender policy."}),
            ])
        db.commit()
        print(f"Seed complete. Case id: {case.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
