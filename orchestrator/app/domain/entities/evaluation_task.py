from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestrator.app.domain.enums import EvaluationTaskStatus


@dataclass(slots=True, frozen=True)
class EvaluationTask:
    evaluation_task_id: str
    job_id: int
    round_id: str | None
    source_training_task_id: str | None
    evaluator_node_id: str | None
    status: EvaluationTaskStatus
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
