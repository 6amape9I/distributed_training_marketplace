from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RoundResponse(BaseModel):
    round_id: str
    job_id: int
    protocol_name: str
    round_index: int
    status: str
    base_model_artifact_uri: str
    aggregated_model_artifact_uri: str | None = None
    aggregated_model_artifact_hash: str | None = None
    evaluation_report_id: str | None = None
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProtocolRunResponse(BaseModel):
    job_id: int
    round_id: str
    task_ids: list[str]
    artifact_ids: list[str]


class RoundReconcileResponse(BaseModel):
    round_id: str
    status: str
    failure_reason: str | None = None
