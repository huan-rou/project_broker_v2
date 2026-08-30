"""initial thin-slice schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(length=255), nullable=False, unique=True), sa.Column("display_name", sa.String(length=255), nullable=False), sa.Column("role", sa.String(length=50), nullable=False, server_default="broker"), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("client_cases", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(length=255), nullable=False), sa.Column("status", sa.String(length=50), nullable=False, server_default="active"), sa.Column("notes", sa.Text(), nullable=True), sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("documents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("case_id", sa.Integer(), sa.ForeignKey("client_cases.id"), nullable=False), sa.Column("original_filename", sa.String(length=500), nullable=False), sa.Column("storage_path", sa.String(length=1000), nullable=False), sa.Column("status", sa.String(length=80), nullable=False, server_default="uploaded"), sa.Column("document_category", sa.String(length=80), nullable=True), sa.Column("ocr_text", sa.Text(), nullable=True), sa.Column("evidence_json", sa.JSON(), nullable=True), sa.Column("fact_find_preview", sa.JSON(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("job_traces", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False), sa.Column("stage", sa.String(length=100), nullable=False), sa.Column("status", sa.String(length=80), nullable=False), sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("error_code", sa.String(length=120), nullable=True), sa.Column("message", sa.String(length=1000), nullable=False), sa.Column("log_summary", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("fact_find_snapshots", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("case_id", sa.Integer(), sa.ForeignKey("client_cases.id"), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("form_data", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("case_id", "version", name="uq_fact_find_case_version"))
    op.create_table("calculator_results", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("case_id", sa.Integer(), sa.ForeignKey("client_cases.id"), nullable=False), sa.Column("lender", sa.String(length=120), nullable=False), sa.Column("status", sa.String(length=80), nullable=False), sa.Column("max_borrowing_capacity", sa.Integer(), nullable=False), sa.Column("monthly_surplus", sa.Integer(), nullable=False), sa.Column("assessment_rate", sa.Float(), nullable=False), sa.Column("notes", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))


def downgrade() -> None:
    op.drop_table("calculator_results")
    op.drop_table("fact_find_snapshots")
    op.drop_table("job_traces")
    op.drop_table("documents")
    op.drop_table("client_cases")
    op.drop_table("users")
