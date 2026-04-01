from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from orchestrator.app.domain.entities import Node
from orchestrator.app.domain.enums import NodeRole, NodeStatus
from orchestrator.app.domain.repositories import NodeRepository


class NodeRegistryService:
    def __init__(self, repository: NodeRepository) -> None:
        self.repository = repository

    def register(
        self,
        *,
        node_id: str,
        role: NodeRole,
        endpoint_url: str,
        capabilities: dict[str, Any] | None,
    ) -> Node:
        now = datetime.now(timezone.utc)
        existing = self.repository.get(node_id)
        node = Node(
            node_id=node_id,
            role=role,
            endpoint_url=endpoint_url,
            capabilities=capabilities,
            status=NodeStatus.REGISTERED if existing is None else existing.status,
            last_seen_at=now,
            created_at=existing.created_at if existing else None,
            updated_at=existing.updated_at if existing else None,
        )
        return self.repository.upsert(node)

    def heartbeat(self, node_id: str) -> Node | None:
        existing = self.repository.get(node_id)
        if existing is None:
            return None
        now = datetime.now(timezone.utc)
        node = Node(
            node_id=existing.node_id,
            role=existing.role,
            endpoint_url=existing.endpoint_url,
            capabilities=existing.capabilities,
            status=NodeStatus.ONLINE,
            last_seen_at=now,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        return self.repository.upsert(node)
