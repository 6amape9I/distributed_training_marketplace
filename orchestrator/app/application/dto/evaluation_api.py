from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationTaskClaimRequest(BaseModel):
    evaluator_node_id: str = Field(min_length=1, max_length=128)


class EvaluationTaskStartRequest(BaseModel):
    evaluator_node_id: str = Field(min_length=1, max_length=128)


class EvaluationTaskCompleteRequest(BaseModel):
    evaluator_node_id: str = Field(min_length=1, max_length=128)
    report_artifact_id: str = Field(min_length=1, max_length=128)
    metrics_json: dict[str, float | int | bool | str]
    sample_count: int = Field(ge=1)
    acceptance_decision: bool
    target_model_digest: str = Field(min_length=1)


class EvaluationTaskFailRequest(BaseModel):
    evaluator_node_id: str = Field(min_length=1, max_length=128)
    failure_reason: str = Field(min_length=1, max_length=1000)


class EvaluationTaskSeedResponse(BaseModel):
    job_id: int
    evaluation_task_ids: list[str]
    artifact_ids: list[str]


class EvaluationTaskResponse(BaseModel):
    evaluation_task_id: str
    job_id: int
    source_training_task_id: str
    evaluator_node_id: str | None = None
    status: str
    target_model_artifact_uri: str
    dataset_artifact_uri: str
    config_json: dict[str, Any]
    report_artifact_uri: str | None = None
    report_artifact_hash: str | None = None
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
