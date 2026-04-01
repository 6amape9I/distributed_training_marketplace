from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from orchestrator.app.domain.entities import EvaluationTask, Round, TrainingTask


@dataclass(slots=True, frozen=True)
class RoundPlan:
    round_record: Round
    task_count: int
    artifact_ids: list[str]


@dataclass(slots=True, frozen=True)
class AggregationArtifacts:
    artifact_id: str
    artifact_uri: str
    artifact_hash: str
    trainer_task_ids: list[str]
    sample_count: int


@dataclass(slots=True, frozen=True)
class AggregationResult:
    round_record: Round
    artifact_id: str
    aggregated_model_artifact_uri: str
    aggregated_model_artifact_hash: str
    trainer_task_ids: list[str]
    metadata: dict[str, Any]


@dataclass(slots=True, frozen=True)
class EvaluationSeedResult:
    round_record: Round
    evaluation_tasks: list[EvaluationTask]
    artifact_ids: list[str]


@dataclass(slots=True, frozen=True)
class ProtocolRunResult:
    round_record: Round
    training_tasks: list[TrainingTask]
    artifact_ids: list[str]
