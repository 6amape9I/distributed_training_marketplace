from __future__ import annotations

from typing import Protocol

from orchestrator.app.application.protocol_runtime.types import AggregationArtifacts
from orchestrator.app.domain.entities import Round, TrainingTask


class AggregationStrategy(Protocol):
    def aggregate(self, round_record: Round, tasks: list[TrainingTask]) -> AggregationArtifacts: ...
