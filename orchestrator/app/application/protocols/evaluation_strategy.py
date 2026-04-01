from __future__ import annotations

from typing import Protocol

from orchestrator.app.application.protocol_runtime.types import EvaluationSeedResult
from orchestrator.app.domain.entities import Round


class EvaluationStrategy(Protocol):
    def seed_evaluation(self, round_record: Round) -> EvaluationSeedResult: ...
