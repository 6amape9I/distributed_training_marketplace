from dataclasses import dataclass
from typing import Any

from orchestrator.app.domain.enums import OnchainJobStatus


@dataclass(slots=True, frozen=True)
class ChainEvent:
    event_name: str
    block_number: int
    transaction_hash: str
    log_index: int
    args: dict[str, Any]

    @property
    def job_id(self) -> int | None:
        raw_job_id = self.args.get("jobId")
        return int(raw_job_id) if raw_job_id is not None else None


@dataclass(slots=True, frozen=True)
class ChainJobSnapshot:
    job_id: int
    requester: str
    provider: str
    attestor: str
    target_escrow_wei: int
    escrow_balance_wei: int
    job_spec_hash: str
    attestation_hash: str | None
    settlement_hash: str | None
    provider_payout_wei: int
    requester_refund_wei: int
    onchain_status: OnchainJobStatus
