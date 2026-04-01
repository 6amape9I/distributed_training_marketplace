"""stage4 evaluation tasks and reports

Revision ID: 20260401_000003
Revises: 20260401_000002
Create Date: 2026-04-01 00:00:03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_000003"
down_revision = "20260401_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_tasks",
        sa.Column("evaluation_task_id", sa.String(length=128), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("source_training_task_id", sa.String(length=128), nullable=False),
        sa.Column("evaluator_node_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("target_model_artifact_uri", sa.Text(), nullable=False),
        sa.Column("dataset_artifact_uri", sa.Text(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("report_artifact_uri", sa.Text(), nullable=True),
        sa.Column("report_artifact_hash", sa.String(length=128), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluation_tasks_job_id", "evaluation_tasks", ["job_id"])
    op.create_index("ix_evaluation_tasks_status", "evaluation_tasks", ["status"])
    op.create_table(
        "evaluation_reports",
        sa.Column("report_id", sa.String(length=128), primary_key=True),
        sa.Column("evaluation_task_id", sa.String(length=128), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("source_training_task_id", sa.String(length=128), nullable=False),
        sa.Column("evaluator_node_id", sa.String(length=128), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("acceptance_decision", sa.Boolean(), nullable=False),
        sa.Column("target_model_digest", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluation_reports_job_id", "evaluation_reports", ["job_id"])
    op.create_index("ix_evaluation_reports_task_id", "evaluation_reports", ["evaluation_task_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_reports_task_id", table_name="evaluation_reports")
    op.drop_index("ix_evaluation_reports_job_id", table_name="evaluation_reports")
    op.drop_table("evaluation_reports")
    op.drop_index("ix_evaluation_tasks_status", table_name="evaluation_tasks")
    op.drop_index("ix_evaluation_tasks_job_id", table_name="evaluation_tasks")
    op.drop_table("evaluation_tasks")
