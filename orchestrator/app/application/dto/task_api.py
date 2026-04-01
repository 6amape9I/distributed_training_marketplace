from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskClaimRequest(BaseModel):
    trainer_node_id: str = Field(min_length=1, max_length=128)


class TaskStartRequest(BaseModel):
    trainer_node_id: str = Field(min_length=1, max_length=128)


class TaskCompleteRequest(BaseModel):
    trainer_node_id: str = Field(min_length=1, max_length=128)
    result_artifact_id: str = Field(min_length=1, max_length=128)
    report_artifact_id: str = Field(min_length=1, max_length=128)


class TaskFailRequest(BaseModel):
    trainer_node_id: str = Field(min_length=1, max_length=128)
    failure_reason: str = Field(min_length=1, max_length=1000)


class TaskSeedResponse(BaseModel):
    job_id: int
    task_ids: list[str]
    artifact_ids: list[str]


class TrainingTaskResponse(BaseModel):
    task_id: str
    job_id: int
    round_id: str | None = None
    trainer_node_id: str | None = None
    task_type: str
    status: str
    data_partition_id: str | None = None
    model_artifact_uri: str
    dataset_artifact_uri: str
    config_json: dict[str, Any]
    result_artifact_uri: str | None = None
    result_artifact_hash: str | None = None
    report_artifact_uri: str | None = None
    report_artifact_hash: str | None = None
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
