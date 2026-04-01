from __future__ import annotations

from orchestrator.app.domain.entities import EvaluationTask
from orchestrator.app.domain.enums import EvaluationTaskStatus, NodeRole, NodeStatus
from orchestrator.app.domain.repositories import EvaluationTaskRepository, NodeRepository


class EvaluationClaimError(ValueError):
    pass


class EvaluationClaimService:
    def __init__(self, tasks: EvaluationTaskRepository, nodes: NodeRepository) -> None:
        self.tasks = tasks
        self.nodes = nodes

    def claim_next(self, evaluator_node_id: str) -> EvaluationTask | None:
        node = self.nodes.get(evaluator_node_id)
        if node is None:
            raise EvaluationClaimError("evaluator node not found")
        if node.role != NodeRole.EVALUATOR:
            raise EvaluationClaimError("node is not an evaluator")
        if node.status != NodeStatus.ONLINE:
            raise EvaluationClaimError("evaluator node is not online")
        return self.tasks.claim_next_pending(evaluator_node_id)
