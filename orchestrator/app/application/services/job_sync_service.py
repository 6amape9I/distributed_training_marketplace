from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from orchestrator.app.domain.entities import ChainSyncState, Job, JobEventRecord
from orchestrator.app.domain.enums import OffchainJobStatus, OnchainJobStatus
from orchestrator.app.domain.repositories import JobEventRepository, JobRepository, SyncStateRepository
from orchestrator.app.infrastructure.blockchain import ChainEvent, ChainJobSnapshot, TrainingMarketplaceClient

from .job_lifecycle_service import JobLifecycleService


@dataclass(slots=True, frozen=True)
class SyncRunResult:
    from_block: int
    to_block: int
    processed_events: int
    skipped_events: int
    latest_block: int


class JobSyncService:
    def __init__(
        self,
        *,
        blockchain: TrainingMarketplaceClient,
        jobs: JobRepository,
        sync_state: SyncStateRepository,
        job_events: JobEventRepository,
        lifecycle: JobLifecycleService,
        chain_id: int,
        contract_address: str,
        start_block: int,
        batch_size: int,
    ) -> None:
        self.blockchain = blockchain
        self.jobs = jobs
        self.sync_state = sync_state
        self.job_events = job_events
        self.lifecycle = lifecycle
        self.chain_id = chain_id
        self.contract_address = contract_address
        self.start_block = start_block
        self.batch_size = batch_size

    @property
    def sync_key(self) -> str:
        return f"{self.chain_id}:{self.contract_address.lower()}"

    def run_once(self) -> SyncRunResult:
        state = self.sync_state.get(self.sync_key)
        latest_block = self.blockchain.get_latest_block()
        from_block = self.start_block if state is None else state.last_processed_block + 1

        if from_block > latest_block:
            return SyncRunResult(
                from_block=from_block,
                to_block=from_block - 1,
                processed_events=0,
                skipped_events=0,
                latest_block=latest_block,
            )

        to_block = min(from_block + self.batch_size - 1, latest_block)
        events = self.blockchain.fetch_events(from_block=from_block, to_block=to_block)

        processed = 0
        skipped = 0
        for event in events:
            if self.job_events.exists(event.transaction_hash, event.log_index):
                skipped += 1
                continue
            self._apply_event(event)
            self.job_events.add(
                JobEventRecord(
                    event_name=event.event_name,
                    transaction_hash=event.transaction_hash,
                    log_index=event.log_index,
                    block_number=event.block_number,
                    job_id=event.job_id,
                    payload=_serialize_event_args(event.args),
                )
            )
            processed += 1

        self.sync_state.upsert(
            ChainSyncState(
                sync_key=self.sync_key,
                chain_id=self.chain_id,
                contract_address=self.contract_address,
                last_processed_block=to_block,
            )
        )
        return SyncRunResult(
            from_block=from_block,
            to_block=to_block,
            processed_events=processed,
            skipped_events=skipped,
            latest_block=latest_block,
        )

    def _apply_event(self, event: ChainEvent) -> None:
        if event.event_name == "JobCreated":
            self._apply_job_created(event)
            return
        if event.event_name == "JobFunded":
            self._apply_job_funded(event)
            return
        if event.event_name == "JobFullyFunded":
            self._apply_job_fully_funded(event)
            return
        if event.event_name == "AttestationSubmitted":
            self._apply_attestation_submitted(event)
            return
        if event.event_name == "JobFinalized":
            self._apply_job_finalized(event)
            return
        if event.event_name in {"PayoutWithdrawn", "RefundWithdrawn"}:
            job = self._require_job(event.job_id)
            self.jobs.upsert(_copy_job(job, last_chain_block=event.block_number))
            return
        raise ValueError(f"Unsupported event: {event.event_name}")

    def _apply_job_created(self, event: ChainEvent) -> None:
        args = event.args
        job = Job(
            job_id=int(args["jobId"]),
            requester=args["requester"],
            provider=args["provider"],
            attestor=args["attestor"],
            target_escrow_wei=int(args["targetEscrow"]),
            escrow_balance_wei=0,
            job_spec_hash=args["jobSpecHash"],
            onchain_status=OnchainJobStatus.OPEN,
            offchain_status=self.lifecycle.status_for_created_job(),
            last_chain_block=event.block_number,
        )
        self.jobs.upsert(job)

    def _apply_job_funded(self, event: ChainEvent) -> None:
        snapshot = self._load_or_fetch_job(event.job_id)
        existing = self.jobs.get(snapshot.job_id)
        offchain_status = self.lifecycle.status_for_funding(
            is_fully_funded=int(event.args["escrowBalance"]) >= snapshot.target_escrow_wei
        )
        self.jobs.upsert(
            Job(
                job_id=snapshot.job_id,
                requester=snapshot.requester,
                provider=snapshot.provider,
                attestor=snapshot.attestor,
                target_escrow_wei=snapshot.target_escrow_wei,
                escrow_balance_wei=int(event.args["escrowBalance"]),
                job_spec_hash=snapshot.job_spec_hash,
                onchain_status=OnchainJobStatus.OPEN,
                offchain_status=offchain_status if existing is None else self.lifecycle.transition(existing.offchain_status, offchain_status),
                attestation_hash=snapshot.attestation_hash,
                settlement_hash=snapshot.settlement_hash,
                provider_payout_wei=snapshot.provider_payout_wei,
                requester_refund_wei=snapshot.requester_refund_wei,
                last_chain_block=event.block_number,
                created_at=existing.created_at if existing else None,
                updated_at=existing.updated_at if existing else None,
            )
        )

    def _apply_job_fully_funded(self, event: ChainEvent) -> None:
        snapshot = self._load_or_fetch_job(event.job_id)
        existing = self._require_job(event.job_id)
        self.jobs.upsert(
            Job(
                job_id=snapshot.job_id,
                requester=snapshot.requester,
                provider=snapshot.provider,
                attestor=snapshot.attestor,
                target_escrow_wei=snapshot.target_escrow_wei,
                escrow_balance_wei=int(event.args["escrowBalance"]),
                job_spec_hash=snapshot.job_spec_hash,
                onchain_status=OnchainJobStatus.FUNDED,
                offchain_status=self.lifecycle.transition(existing.offchain_status, OffchainJobStatus.FUNDED),
                attestation_hash=snapshot.attestation_hash,
                settlement_hash=snapshot.settlement_hash,
                provider_payout_wei=snapshot.provider_payout_wei,
                requester_refund_wei=snapshot.requester_refund_wei,
                last_chain_block=event.block_number,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )
        )

    def _apply_attestation_submitted(self, event: ChainEvent) -> None:
        snapshot = self._load_or_fetch_job(event.job_id)
        existing = self._require_job(event.job_id)
        self.jobs.upsert(
            Job(
                job_id=snapshot.job_id,
                requester=snapshot.requester,
                provider=snapshot.provider,
                attestor=snapshot.attestor,
                target_escrow_wei=snapshot.target_escrow_wei,
                escrow_balance_wei=snapshot.escrow_balance_wei,
                job_spec_hash=snapshot.job_spec_hash,
                onchain_status=OnchainJobStatus.ATTESTED,
                offchain_status=self.lifecycle.transition(existing.offchain_status, OffchainJobStatus.ATTESTED),
                attestation_hash=event.args["attestationHash"],
                settlement_hash=snapshot.settlement_hash,
                provider_payout_wei=snapshot.provider_payout_wei,
                requester_refund_wei=snapshot.requester_refund_wei,
                last_chain_block=event.block_number,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )
        )

    def _apply_job_finalized(self, event: ChainEvent) -> None:
        snapshot = self._load_or_fetch_job(event.job_id)
        existing = self._require_job(event.job_id)
        self.jobs.upsert(
            Job(
                job_id=snapshot.job_id,
                requester=snapshot.requester,
                provider=snapshot.provider,
                attestor=snapshot.attestor,
                target_escrow_wei=snapshot.target_escrow_wei,
                escrow_balance_wei=snapshot.escrow_balance_wei,
                job_spec_hash=snapshot.job_spec_hash,
                onchain_status=OnchainJobStatus.FINALIZED,
                offchain_status=self.lifecycle.transition(existing.offchain_status, OffchainJobStatus.FINALIZED),
                attestation_hash=snapshot.attestation_hash,
                settlement_hash=event.args["settlementHash"],
                provider_payout_wei=int(event.args["providerPayout"]),
                requester_refund_wei=int(event.args["requesterRefund"]),
                last_chain_block=event.block_number,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )
        )

    def _load_or_fetch_job(self, job_id: int | None) -> ChainJobSnapshot:
        if job_id is None:
            raise ValueError("Expected job event to contain jobId")
        return self.blockchain.get_job(job_id)

    def _require_job(self, job_id: int | None) -> Job:
        if job_id is None:
            raise ValueError("Expected job event to contain jobId")
        existing = self.jobs.get(job_id)
        if existing is None:
            snapshot = self.blockchain.get_job(job_id)
            bootstrap = Job(
                job_id=snapshot.job_id,
                requester=snapshot.requester,
                provider=snapshot.provider,
                attestor=snapshot.attestor,
                target_escrow_wei=snapshot.target_escrow_wei,
                escrow_balance_wei=snapshot.escrow_balance_wei,
                job_spec_hash=snapshot.job_spec_hash,
                onchain_status=snapshot.onchain_status,
                offchain_status=self.lifecycle.status_for_onchain_progress(snapshot.onchain_status),
                attestation_hash=snapshot.attestation_hash,
                settlement_hash=snapshot.settlement_hash,
                provider_payout_wei=snapshot.provider_payout_wei,
                requester_refund_wei=snapshot.requester_refund_wei,
            )
            return self.jobs.upsert(bootstrap)
        return existing


def _copy_job(job: Job, **changes: Any) -> Job:
    payload = {
        "job_id": job.job_id,
        "requester": job.requester,
        "provider": job.provider,
        "attestor": job.attestor,
        "target_escrow_wei": job.target_escrow_wei,
        "escrow_balance_wei": job.escrow_balance_wei,
        "job_spec_hash": job.job_spec_hash,
        "onchain_status": job.onchain_status,
        "offchain_status": job.offchain_status,
        "attestation_hash": job.attestation_hash,
        "settlement_hash": job.settlement_hash,
        "provider_payout_wei": job.provider_payout_wei,
        "requester_refund_wei": job.requester_refund_wei,
        "last_chain_block": job.last_chain_block,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
    payload.update(changes)
    return Job(**payload)


def _serialize_event_args(args: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in args.items():
        if isinstance(value, (bytes, bytearray)):
            result[key] = "0x" + bytes(value).hex()
        else:
            result[key] = value
    return result
