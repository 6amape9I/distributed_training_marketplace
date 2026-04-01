"""stage2 initial orchestrator schema"""

from alembic import op
import sqlalchemy as sa

revision = "20260401_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("requester", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("attestor", sa.String(length=128), nullable=False),
        sa.Column("target_escrow_wei", sa.BigInteger(), nullable=False),
        sa.Column("escrow_balance_wei", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("job_spec_hash", sa.String(length=66), nullable=False),
        sa.Column("onchain_status", sa.String(length=32), nullable=False),
        sa.Column("offchain_status", sa.String(length=64), nullable=False),
        sa.Column("attestation_hash", sa.String(length=66), nullable=True),
        sa.Column("settlement_hash", sa.String(length=66), nullable=True),
        sa.Column("provider_payout_wei", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("requester_refund_wei", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("last_chain_block", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_table(
        "nodes",
        sa.Column("node_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("endpoint_url", sa.Text(), nullable=False),
        sa.Column("capabilities_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("node_id"),
    )
    op.create_table(
        "chain_sync_state",
        sa.Column("sync_key", sa.String(length=255), nullable=False),
        sa.Column("chain_id", sa.BigInteger(), nullable=False),
        sa.Column("contract_address", sa.String(length=128), nullable=False),
        sa.Column("last_processed_block", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("sync_key"),
    )
    op.create_table(
        "job_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_name", sa.String(length=64), nullable=False),
        sa.Column("transaction_hash", sa.String(length=66), nullable=False),
        sa.Column("log_index", sa.Integer(), nullable=False),
        sa.Column("block_number", sa.BigInteger(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_hash", "log_index", name="uq_job_events_tx_log"),
    )


def downgrade() -> None:
    op.drop_table("job_events")
    op.drop_table("chain_sync_state")
    op.drop_table("nodes")
    op.drop_table("jobs")
