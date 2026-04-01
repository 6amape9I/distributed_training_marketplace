from datetime import datetime

from pydantic import BaseModel


class JobSummaryResponse(BaseModel):
    job_id: int
    onchain_status: str
    offchain_status: str
    escrow_balance_wei: int
    target_escrow_wei: int
    updated_at: datetime | None = None


class JobDetailResponse(JobSummaryResponse):
    requester: str
    provider: str
    attestor: str
    job_spec_hash: str
    attestation_hash: str | None = None
    settlement_hash: str | None = None
    provider_payout_wei: int
    requester_refund_wei: int
    last_chain_block: int


class SyncResponse(BaseModel):
    from_block: int
    to_block: int
    processed_events: int
    skipped_events: int
    latest_block: int
