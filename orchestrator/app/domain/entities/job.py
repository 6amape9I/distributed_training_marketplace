from dataclasses import dataclass
from datetime import datetime

from orchestrator.app.domain.enums import OffchainJobStatus, OnchainJobStatus


@dataclass(slots=True, frozen=True)
class Job:
    job_id: int
    requester: str
    provider: str
    attestor: str
    target_escrow_wei: int
    escrow_balance_wei: int
    job_spec_hash: str
    onchain_status: OnchainJobStatus
    offchain_status: OffchainJobStatus
    attestation_hash: str | None = None
    settlement_hash: str | None = None
    provider_payout_wei: int = 0
    requester_refund_wei: int = 0
    last_chain_block: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
