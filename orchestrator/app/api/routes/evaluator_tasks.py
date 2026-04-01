from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from orchestrator.app.api.deps import get_evaluation_claim_service, get_evaluation_completion_service
from orchestrator.app.application.dto import (
    EvaluationTaskClaimRequest,
    EvaluationTaskCompleteRequest,
    EvaluationTaskFailRequest,
    EvaluationTaskResponse,
    EvaluationTaskStartRequest,
)
from orchestrator.app.application.services import (
    EvaluationClaimError,
    EvaluationClaimService,
    EvaluationCompletionError,
    EvaluationCompletionService,
)
from orchestrator.app.domain.entities import EvaluationTask

router = APIRouter(prefix="/evaluator/tasks", tags=["evaluator-tasks"])


def _to_response(task: EvaluationTask) -> EvaluationTaskResponse:
    return EvaluationTaskResponse(
        evaluation_task_id=task.evaluation_task_id,
        job_id=task.job_id,
        source_training_task_id=task.source_training_task_id,
        evaluator_node_id=task.evaluator_node_id,
        status=task.status.value,
        target_model_artifact_uri=task.target_model_artifact_uri,
        dataset_artifact_uri=task.dataset_artifact_uri,
        config_json=task.config_json,
        report_artifact_uri=task.report_artifact_uri,
        report_artifact_hash=task.report_artifact_hash,
        claimed_at=task.claimed_at,
        completed_at=task.completed_at,
        failure_reason=task.failure_reason,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("/claim", response_model=EvaluationTaskResponse | None)
def claim_evaluation_task(
    payload: EvaluationTaskClaimRequest,
    service: Annotated[EvaluationClaimService, Depends(get_evaluation_claim_service)],
) -> EvaluationTaskResponse | None:
    try:
        task = service.claim_next(payload.evaluator_node_id)
    except EvaluationClaimError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if task is None:
        return None
    return _to_response(task)


@router.post("/{evaluation_task_id}/start", response_model=EvaluationTaskResponse)
def start_evaluation_task(
    evaluation_task_id: str,
    payload: EvaluationTaskStartRequest,
    service: Annotated[EvaluationCompletionService, Depends(get_evaluation_completion_service)],
) -> EvaluationTaskResponse:
    try:
        return _to_response(service.start(evaluation_task_id, payload.evaluator_node_id))
    except EvaluationCompletionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{evaluation_task_id}/complete", response_model=EvaluationTaskResponse)
def complete_evaluation_task(
    evaluation_task_id: str,
    payload: EvaluationTaskCompleteRequest,
    service: Annotated[EvaluationCompletionService, Depends(get_evaluation_completion_service)],
) -> EvaluationTaskResponse:
    try:
        return _to_response(
            service.complete(
                evaluation_task_id,
                payload.evaluator_node_id,
                payload.report_artifact_id,
                payload.metrics_json,
                payload.sample_count,
                payload.acceptance_decision,
                payload.target_model_digest,
            )
        )
    except EvaluationCompletionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{evaluation_task_id}/fail", response_model=EvaluationTaskResponse)
def fail_evaluation_task(
    evaluation_task_id: str,
    payload: EvaluationTaskFailRequest,
    service: Annotated[EvaluationCompletionService, Depends(get_evaluation_completion_service)],
) -> EvaluationTaskResponse:
    try:
        return _to_response(service.fail(evaluation_task_id, payload.evaluator_node_id, payload.failure_reason))
    except EvaluationCompletionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{evaluation_task_id}", response_model=EvaluationTaskResponse)
def get_evaluation_task(
    evaluation_task_id: str,
    service: Annotated[EvaluationCompletionService, Depends(get_evaluation_completion_service)],
) -> EvaluationTaskResponse:
    task = service.get(evaluation_task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="evaluation task not found")
    return _to_response(task)
