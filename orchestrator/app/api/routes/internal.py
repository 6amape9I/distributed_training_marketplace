from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from orchestrator.app.api.deps import get_orchestration_coordinator, get_task_dispatch_service
from orchestrator.app.application.dto import ReconcileResponse, SyncResponse, TaskSeedResponse
from orchestrator.app.application.services import OrchestrationCoordinator, TaskDispatchError, TaskDispatchService

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/sync/run-once", response_model=SyncResponse)
def sync_run_once(
    coordinator: Annotated[OrchestrationCoordinator, Depends(get_orchestration_coordinator)],
) -> SyncResponse:
    result = coordinator.run_sync_once()
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
) -> ReconcileResponse:
    return ReconcileResponse(changed_jobs=coordinator.reconcile_lifecycle())


@router.post("/tasks/seed-for-job/{job_id}", response_model=TaskSeedResponse)
def seed_demo_tasks_for_job(
    job_id: int,
    service: Annotated[TaskDispatchService, Depends(get_task_dispatch_service)],
) -> TaskSeedResponse:
    try:
        tasks, artifact_ids = service.seed_demo_tasks_for_job(job_id)
    except TaskDispatchError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TaskSeedResponse(job_id=job_id, task_ids=[task.task_id for task in tasks], artifact_ids=artifact_ids)
