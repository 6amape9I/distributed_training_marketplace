from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EvaluationTaskRecord(BaseModel):
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
