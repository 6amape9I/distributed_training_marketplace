from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from orchestrator.app.api.deps import (
    get_db_session,
    get_evaluation_dispatch_service,
    get_orchestration_coordinator,
    get_protocol_run_service,
    get_round_reconciliation_service,
    get_task_dispatch_service,
)
from orchestrator.app.application.dto import (
    EvaluationTaskSeedResponse,
    ProtocolRunResponse,
    ReconcileResponse,
    RoundReconcileResponse,
    SyncResponse,
    TaskSeedResponse,
)
from orchestrator.app.application.services.protocol_run_service import ProtocolRunService
from orchestrator.app.application.services.round_reconciliation_service import RoundReconciliationError, RoundReconciliationService
from orchestrator.app.application.services import (
    EvaluationDispatchError,
    EvaluationDispatchService,
    OrchestrationCoordinator,
    TaskDispatchError,
    TaskDispatchService,
)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/sync/run-once", response_model=SyncResponse)
def sync_run_once(
    coordinator: Annotated[OrchestrationCoordinator, Depends(get_orchestration_coordinator)],
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> SyncResponse:
    result = coordinator.run_sync_once()
    if session is not None:
        session.commit()
    return SyncResponse(
        from_block=result.from_block,
        to_block=result.to_block,
        processed_events=result.processed_events,
        skipped_events=result.skipped_events,
        latest_block=result.latest_block,
    )


@router.post("/lifecycle/reconcile", response_model=ReconcileResponse)
def reconcile_lifecycle(
    coordinator: Annotated[OrchestrationCoordinator, Depends(get_orchestration_coordinator)],
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> ReconcileResponse:
    changed_jobs = coordinator.reconcile_lifecycle()
    if session is not None:
        session.commit()
    return ReconcileResponse(changed_jobs=changed_jobs)


@router.post("/tasks/seed-for-job/{job_id}", response_model=TaskSeedResponse)
def seed_demo_tasks_for_job(
    job_id: int,
    service: Annotated[TaskDispatchService, Depends(get_task_dispatch_service)],
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> TaskSeedResponse:
    try:
        tasks, artifact_ids = service.seed_demo_tasks_for_job(job_id)
    except TaskDispatchError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if session is not None:
        session.commit()
    return TaskSeedResponse(job_id=job_id, task_ids=[task.task_id for task in tasks], artifact_ids=artifact_ids)


@router.post("/evaluations/seed-for-job/{job_id}", response_model=EvaluationTaskSeedResponse)
def seed_evaluation_tasks_for_job(
    job_id: int,
    service: Annotated[EvaluationDispatchService, Depends(get_evaluation_dispatch_service)],
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> EvaluationTaskSeedResponse:
    try:
        tasks, artifact_ids = service.seed_for_job(job_id)
    except EvaluationDispatchError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if session is not None:
        session.commit()
    return EvaluationTaskSeedResponse(
        job_id=job_id,
        evaluation_task_ids=[task.evaluation_task_id for task in tasks],
        artifact_ids=artifact_ids,
    )


@router.post("/protocol-runs/start-for-job/{job_id}", response_model=ProtocolRunResponse)
def start_protocol_run_for_job(
    job_id: int,
    service: Annotated[ProtocolRunService, Depends(get_protocol_run_service)],
    protocol_name: str | None = None,
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> ProtocolRunResponse:
    try:
        result = service.start_for_job(job_id, protocol_name=protocol_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if session is not None:
        session.commit()
    return ProtocolRunResponse(
        job_id=job_id,
        round_id=result.round_record.round_id,
        protocol_name=result.round_record.protocol_name,
        task_ids=[task.task_id for task in result.training_tasks],
        artifact_ids=result.artifact_ids,
    )


@router.post("/rounds/{round_id}/reconcile", response_model=RoundReconcileResponse)
def reconcile_round(
    round_id: str,
    service: Annotated[RoundReconciliationService, Depends(get_round_reconciliation_service)],
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> RoundReconcileResponse:
    try:
        round_record = service.reconcile(round_id)
    except RoundReconciliationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if session is not None:
        session.commit()
    return RoundReconcileResponse(
        round_id=round_record.round_id,
        status=round_record.status.value,
        failure_reason=round_record.failure_reason,
    )
