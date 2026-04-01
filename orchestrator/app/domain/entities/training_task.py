from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestrator.app.domain.enums import TrainingTaskStatus, TrainingTaskType


@dataclass(slots=True, frozen=True)
class TrainingTask:
    task_id: str
    job_id: int
    round_id: str | None
    trainer_node_id: str | None
    task_type: TrainingTaskType
    status: TrainingTaskStatus
    data_partition_id: str | None
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
