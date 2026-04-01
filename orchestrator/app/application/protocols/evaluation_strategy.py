from typing import Protocol

from shared.python.ids import JobId
from shared.python.schemas import ArtifactRef, SettlementDecision


class EvaluationStrategy(Protocol):
    def evaluate(self, job_id: JobId, artifact: ArtifactRef) -> SettlementDecision: ...
