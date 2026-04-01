from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from orchestrator.app.infrastructure.db.base import Base


class JobModel(Base):
    __tablename__ = "jobs"

    job_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requester: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    attestor: Mapped[str] = mapped_column(String(128), nullable=False)
    target_escrow_wei: Mapped[int] = mapped_column(BigInteger, nullable=False)
    escrow_balance_wei: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    job_spec_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    onchain_status: Mapped[str] = mapped_column(String(32), nullable=False)
    offchain_status: Mapped[str] = mapped_column(String(64), nullable=False)
    attestation_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    settlement_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    provider_payout_wei: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    requester_refund_wei: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    last_chain_block: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class NodeModel(Base):
    __tablename__ = "nodes"

    node_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    endpoint_url: Mapped[str] = mapped_column(Text, nullable=False)
    capabilities_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ChainSyncStateModel(Base):
    __tablename__ = "chain_sync_state"

    sync_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    chain_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    contract_address: Mapped[str] = mapped_column(String(128), nullable=False)
    last_processed_block: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class JobEventModel(Base):
    __tablename__ = "job_events"
    __table_args__ = (UniqueConstraint("transaction_hash", "log_index", name="uq_job_events_tx_log"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_name: Mapped[str] = mapped_column(String(64), nullable=False)
    transaction_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    log_index: Mapped[int] = mapped_column(Integer, nullable=False)
    block_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)



class TrainingTaskModel(Base):
    __tablename__ = "training_tasks"

    task_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    trainer_node_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    data_partition_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    dataset_artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    result_artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_artifact_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    report_artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_artifact_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    artifact_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    content_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
