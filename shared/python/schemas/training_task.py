from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TrainingTaskRecord(BaseModel):
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
