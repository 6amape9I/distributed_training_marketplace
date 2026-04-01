from __future__ import annotations

from orchestrator.app.domain.entities import TrainingTask
from orchestrator.app.domain.enums import NodeRole, NodeStatus
from orchestrator.app.domain.repositories import NodeRepository, TrainingTaskRepository


class TaskClaimError(ValueError):
    pass


class TaskClaimService:
    def __init__(self, tasks: TrainingTaskRepository, nodes: NodeRepository) -> None:
        self.tasks = tasks
        self.nodes = nodes

    def claim_next(self, trainer_node_id: str) -> TrainingTask | None:
        node = self.nodes.get(trainer_node_id)
        if node is None:
            raise TaskClaimError("trainer node not found")
        if node.role != NodeRole.TRAINER:
            raise TaskClaimError("node is not a trainer")
        if node.status != NodeStatus.ONLINE:
            raise TaskClaimError("trainer node is not online")
        return self.tasks.claim_next_pending(trainer_node_id)
