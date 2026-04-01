from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from orchestrator.app.domain.enums import RoundStatus


@dataclass(slots=True, frozen=True)
class Round:
    round_id: str
    job_id: int
    protocol_name: str
    round_index: int
    status: RoundStatus
    base_model_artifact_uri: str
    aggregated_model_artifact_uri: str | None = None
    aggregated_model_artifact_hash: str | None = None
    evaluation_report_id: str | None = None
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
