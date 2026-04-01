from __future__ import annotations

from typing import Protocol

from orchestrator.app.application.protocol_runtime.types import AggregationResult, EvaluationSeedResult, ProtocolRunResult, RoundPlan
from orchestrator.app.domain.entities import Job, Node, Round, TrainingTask


class TrainingProtocol(Protocol):
    protocol_name: str

    def start_run_for_job(self, job_id: int) -> ProtocolRunResult: ...

    def prepare_round(self, job: Job, round_record: Round, trainer_count: int) -> RoundPlan: ...

    def seed_training_tasks(self, round_record: Round, trainers: list[Node]) -> list[TrainingTask]: ...

    def aggregate_round(self, round_record: Round) -> AggregationResult: ...

    def seed_evaluation(self, round_record: Round) -> EvaluationSeedResult: ...
