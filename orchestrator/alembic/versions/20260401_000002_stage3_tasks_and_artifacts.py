"""stage3 tasks and artifacts

Revision ID: 20260401_000002
Revises: 20260401_000001
Create Date: 2026-04-01 00:00:02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_000002"
down_revision = "20260401_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_tasks",
        sa.Column("task_id", sa.String(length=128), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("trainer_node_id", sa.String(length=128), nullable=True),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("data_partition_id", sa.String(length=128), nullable=True),
        sa.Column("model_artifact_uri", sa.Text(), nullable=False),
        sa.Column("dataset_artifact_uri", sa.Text(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("result_artifact_uri", sa.Text(), nullable=True),
        sa.Column("result_artifact_hash", sa.String(length=128), nullable=True),
        sa.Column("report_artifact_uri", sa.Text(), nullable=True),
        sa.Column("report_artifact_hash", sa.String(length=128), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_training_tasks_job_id", "training_tasks", ["job_id"])
    op.create_index("ix_training_tasks_status", "training_tasks", ["status"])

    op.create_table(
        "artifacts",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("content_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("task_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_artifacts_task_id", "artifacts", ["task_id"])
    op.create_index("ix_artifacts_job_id", "artifacts", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_artifacts_job_id", table_name="artifacts")
    op.drop_index("ix_artifacts_task_id", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("ix_training_tasks_status", table_name="training_tasks")
    op.drop_index("ix_training_tasks_job_id", table_name="training_tasks")
    op.drop_table("training_tasks")
