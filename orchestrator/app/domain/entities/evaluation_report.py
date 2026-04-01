from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class EvaluationReport:
    report_id: str
    evaluation_task_id: str
    job_id: int
    source_training_task_id: str
    evaluator_node_id: str
    metrics_json: dict[str, float | int | bool | str]
    sample_count: int
    acceptance_decision: bool
    target_model_digest: str
    created_at: datetime | None = None
