from orchestrator.app.application.services import JobLifecycleService, JobSyncService
from orchestrator.app.domain.enums import OffchainJobStatus, OnchainJobStatus
from orchestrator.app.infrastructure.blockchain.types import ChainEvent

from .conftest import (
    InMemoryJobEventRepository,
    InMemoryJobRepository,
    InMemorySyncStateRepository,
    build_snapshot,
)


def test_run_once_imports_events_and_is_idempotent(fake_blockchain) -> None:
    snapshot = build_snapshot(onchain_status=OnchainJobStatus.FUNDED, escrow_balance_wei=10)
    fake_blockchain.add_job(snapshot)
    fake_blockchain.add_event(
        ChainEvent(
            event_name="JobCreated",
            block_number=1,
            transaction_hash="0x01",
            log_index=0,
            args={
                "jobId": 1,
                "requester": snapshot.requester,
                "provider": snapshot.provider,
                "attestor": snapshot.attestor,
                "targetEscrow": snapshot.target_escrow_wei,
                "jobSpecHash": snapshot.job_spec_hash,
            },
        )
    )
    fake_blockchain.add_event(
        ChainEvent(
            event_name="JobFunded",
            block_number=2,
            transaction_hash="0x02",
            log_index=0,
            args={"jobId": 1, "funder": snapshot.requester, "amount": 4, "escrowBalance": 4},
        )
    )
    fake_blockchain.add_event(
        ChainEvent(
            event_name="JobFullyFunded",
            block_number=3,
            transaction_hash="0x03",
            log_index=0,
            args={"jobId": 1, "escrowBalance": 10},
        )
    )

    jobs = InMemoryJobRepository()
    sync_state = InMemorySyncStateRepository()
    event_repo = InMemoryJobEventRepository()
    service = JobSyncService(
        blockchain=fake_blockchain,
        jobs=jobs,
        sync_state=sync_state,
        job_events=event_repo,
        lifecycle=JobLifecycleService(),
        chain_id=31337,
        contract_address="0x0000000000000000000000000000000000000001",
        start_block=0,
        batch_size=100,
    )

    first = service.run_once()
    assert first.processed_events == 3
    job = jobs.get(1)
    assert job is not None
    assert job.onchain_status is OnchainJobStatus.FUNDED
    assert job.offchain_status is OffchainJobStatus.FUNDED

    second = service.run_once()
    assert second.processed_events == 0
    assert second.skipped_events == 0


def test_run_once_maps_finalized_event_to_finalized_state(fake_blockchain) -> None:
    snapshot = build_snapshot(
        onchain_status=OnchainJobStatus.FINALIZED,
        settlement_hash="0x" + "2" * 64,
        provider_payout_wei=7,
        requester_refund_wei=3,
    )
    fake_blockchain.add_job(snapshot)
    fake_blockchain.add_event(
        ChainEvent(
            event_name="JobCreated",
            block_number=1,
            transaction_hash="0xaa",
            log_index=0,
            args={
                "jobId": 1,
                "requester": snapshot.requester,
                "provider": snapshot.provider,
                "attestor": snapshot.attestor,
                "targetEscrow": snapshot.target_escrow_wei,
                "jobSpecHash": snapshot.job_spec_hash,
            },
        )
    )
    fake_blockchain.add_event(
        ChainEvent(
            event_name="JobFinalized",
            block_number=2,
            transaction_hash="0xbb",
            log_index=0,
            args={
                "jobId": 1,
                "finalizer": snapshot.attestor,
                "providerPayout": 7,
                "requesterRefund": 3,
                "settlementHash": snapshot.settlement_hash,
            },
        )
    )

    jobs = InMemoryJobRepository()
    service = JobSyncService(
        blockchain=fake_blockchain,
        jobs=jobs,
        sync_state=InMemorySyncStateRepository(),
        job_events=InMemoryJobEventRepository(),
        lifecycle=JobLifecycleService(),
        chain_id=31337,
        contract_address="0x0000000000000000000000000000000000000001",
        start_block=0,
        batch_size=100,
    )

    service.run_once()
    job = jobs.get(1)
    assert job is not None
    assert job.offchain_status is OffchainJobStatus.FINALIZED
    assert job.provider_payout_wei == 7
    assert job.requester_refund_wei == 3
