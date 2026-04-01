from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from orchestrator.app.api.deps import get_db_session, get_job_sync_service
from orchestrator.app.application.dto import JobDetailResponse, JobSummaryResponse, SyncResponse
from orchestrator.app.application.services import JobSyncService
from orchestrator.app.infrastructure.container import AppContainer
from orchestrator.app.api.deps import get_container

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobSummaryResponse])
def list_jobs(
    session: Annotated[Session, Depends(get_db_session)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> list[JobSummaryResponse]:
    jobs = container.job_repository(session).list()
    return [
        JobSummaryResponse(
            job_id=job.job_id,
            onchain_status=job.onchain_status.value,
            offchain_status=job.offchain_status.value,
            escrow_balance_wei=job.escrow_balance_wei,
            target_escrow_wei=job.target_escrow_wei,
            updated_at=job.updated_at,
        )
        for job in jobs
    ]


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(
    job_id: int,
    session: Annotated[Session, Depends(get_db_session)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> JobDetailResponse:
    job = container.job_repository(session).get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return JobDetailResponse(
        job_id=job.job_id,
        onchain_status=job.onchain_status.value,
        offchain_status=job.offchain_status.value,
        escrow_balance_wei=job.escrow_balance_wei,
        target_escrow_wei=job.target_escrow_wei,
        updated_at=job.updated_at,
        requester=job.requester,
        provider=job.provider,
        attestor=job.attestor,
        job_spec_hash=job.job_spec_hash,
        attestation_hash=job.attestation_hash,
        settlement_hash=job.settlement_hash,
        provider_payout_wei=job.provider_payout_wei,
        requester_refund_wei=job.requester_refund_wei,
        last_chain_block=job.last_chain_block,
    )


@router.post("/sync", response_model=SyncResponse)
def sync_jobs(sync_service: Annotated[JobSyncService, Depends(get_job_sync_service)]) -> SyncResponse:
    result = sync_service.run_once()
    return SyncResponse(
        from_block=result.from_block,
        to_block=result.to_block,
        processed_events=result.processed_events,
        skipped_events=result.skipped_events,
        latest_block=result.latest_block,
    )
