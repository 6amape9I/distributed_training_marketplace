"""stage5 rounds and protocol links

Revision ID: 20260401_000004
Revises: 20260401_000003
Create Date: 2026-04-01 00:00:04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_000004"
down_revision = "20260401_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rounds",
        sa.Column("round_id", sa.String(length=128), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("protocol_name", sa.String(length=128), nullable=False),
        sa.Column("round_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("base_model_artifact_uri", sa.Text(), nullable=False),
        sa.Column("aggregated_model_artifact_uri", sa.Text(), nullable=True),
        sa.Column("aggregated_model_artifact_hash", sa.String(length=128), nullable=True),
        sa.Column("evaluation_report_id", sa.String(length=128), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rounds_job_id", "rounds", ["job_id"])
    op.create_index("ix_rounds_status", "rounds", ["status"])

    with op.batch_alter_table("training_tasks") as batch_op:
        batch_op.add_column(sa.Column("round_id", sa.String(length=128), nullable=True))
        batch_op.create_index("ix_training_tasks_round_id", ["round_id"], unique=False)

    with op.batch_alter_table("evaluation_tasks") as batch_op:
        batch_op.add_column(sa.Column("round_id", sa.String(length=128), nullable=True))
        batch_op.alter_column("source_training_task_id", existing_type=sa.String(length=128), nullable=True)
        batch_op.create_index("ix_evaluation_tasks_round_id", ["round_id"], unique=False)

    with op.batch_alter_table("evaluation_reports") as batch_op:
        batch_op.add_column(sa.Column("round_id", sa.String(length=128), nullable=True))
        batch_op.alter_column("source_training_task_id", existing_type=sa.String(length=128), nullable=True)
        batch_op.create_index("ix_evaluation_reports_round_id", ["round_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("evaluation_reports") as batch_op:
        batch_op.drop_index("ix_evaluation_reports_round_id")
        batch_op.alter_column("source_training_task_id", existing_type=sa.String(length=128), nullable=False)
        batch_op.drop_column("round_id")

    with op.batch_alter_table("evaluation_tasks") as batch_op:
        batch_op.drop_index("ix_evaluation_tasks_round_id")
        batch_op.alter_column("source_training_task_id", existing_type=sa.String(length=128), nullable=False)
        batch_op.drop_column("round_id")

    with op.batch_alter_table("training_tasks") as batch_op:
        batch_op.drop_index("ix_training_tasks_round_id")
        batch_op.drop_column("round_id")

    op.drop_index("ix_rounds_status", table_name="rounds")
    op.drop_index("ix_rounds_job_id", table_name="rounds")
    op.drop_table("rounds")
