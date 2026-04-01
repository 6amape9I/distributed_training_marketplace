from typing import Annotated

from fastapi import APIRouter, Depends

from orchestrator.app.api.deps import get_orchestration_coordinator
from orchestrator.app.application.dto import ReconcileResponse, SyncResponse
from orchestrator.app.application.services import OrchestrationCoordinator

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
