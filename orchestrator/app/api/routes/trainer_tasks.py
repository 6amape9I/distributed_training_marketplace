from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from orchestrator.app.api.deps import get_task_claim_service, get_task_completion_service
from orchestrator.app.application.dto import (
    TaskClaimRequest,
    TaskCompleteRequest,
    TaskFailRequest,
    TaskStartRequest,
    TrainingTaskResponse,
)
from orchestrator.app.application.services import (
    TaskClaimError,
    TaskClaimService,
    TaskCompletionError,
    TaskCompletionService,
)
from orchestrator.app.domain.entities import TrainingTask

router = APIRouter(prefix="/trainer/tasks", tags=["trainer-tasks"])


def _to_response(task: TrainingTask) -> TrainingTaskResponse:
    return TrainingTaskResponse(
        task_id=task.task_id,
        job_id=task.job_id,
        round_id=task.round_id,
        trainer_node_id=task.trainer_node_id,
        task_type=task.task_type.value,
        status=task.status.value,
        data_partition_id=task.data_partition_id,
        model_artifact_uri=task.model_artifact_uri,
        dataset_artifact_uri=task.dataset_artifact_uri,
        config_json=task.config_json,
        result_artifact_uri=task.result_artifact_uri,
        result_artifact_hash=task.result_artifact_hash,
        report_artifact_uri=task.report_artifact_uri,
        report_artifact_hash=task.report_artifact_hash,
        claimed_at=task.claimed_at,
        completed_at=task.completed_at,
        failure_reason=task.failure_reason,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("/claim", response_model=TrainingTaskResponse | None)
def claim_task(
    payload: TaskClaimRequest,
    service: Annotated[TaskClaimService, Depends(get_task_claim_service)],
) -> TrainingTaskResponse | None:
    try:
        task = service.claim_next(payload.trainer_node_id)
    except TaskClaimError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if task is None:
        return None
    return _to_response(task)


@router.post("/{task_id}/start", response_model=TrainingTaskResponse)
def start_task(
    task_id: str,
    payload: TaskStartRequest,
    service: Annotated[TaskCompletionService, Depends(get_task_completion_service)],
) -> TrainingTaskResponse:
    try:
        return _to_response(service.start(task_id, payload.trainer_node_id))
    except TaskCompletionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{task_id}/complete", response_model=TrainingTaskResponse)
def complete_task(
    task_id: str,
    payload: TaskCompleteRequest,
    service: Annotated[TaskCompletionService, Depends(get_task_completion_service)],
) -> TrainingTaskResponse:
    try:
        return _to_response(
            service.complete(task_id, payload.trainer_node_id, payload.result_artifact_id, payload.report_artifact_id)
        )
    except TaskCompletionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{task_id}/fail", response_model=TrainingTaskResponse)
def fail_task(
    task_id: str,
    payload: TaskFailRequest,
    service: Annotated[TaskCompletionService, Depends(get_task_completion_service)],
) -> TrainingTaskResponse:
    try:
        return _to_response(service.fail(task_id, payload.trainer_node_id, payload.failure_reason))
    except TaskCompletionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{task_id}", response_model=TrainingTaskResponse)
def get_task(
    task_id: str,
    service: Annotated[TaskCompletionService, Depends(get_task_completion_service)],
) -> TrainingTaskResponse:
    task = service.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return _to_response(task)
