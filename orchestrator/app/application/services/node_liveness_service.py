from __future__ import annotations

from datetime import datetime, timedelta, timezone

from orchestrator.app.domain.entities import Node
from orchestrator.app.domain.enums import NodeStatus


class NodeLivenessService:
    def __init__(self, stale_after_seconds: int) -> None:
        self.stale_after_seconds = stale_after_seconds

    def derive_status(self, last_seen_at: datetime | None, now: datetime | None = None) -> NodeStatus:
        if last_seen_at is None:
            return NodeStatus.REGISTERED

        current_time = now or datetime.now(timezone.utc)
        if last_seen_at.tzinfo is None:
            last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
        stale_after = timedelta(seconds=self.stale_after_seconds)
        offline_after = stale_after * 2
        age = current_time - last_seen_at

        if age > offline_after:
            return NodeStatus.OFFLINE
        if age > stale_after:
            return NodeStatus.STALE
        return NodeStatus.ONLINE

    def refresh(self, node: Node, now: datetime | None = None) -> Node:
        return Node(
            node_id=node.node_id,
            role=node.role,
            endpoint_url=node.endpoint_url,
            capabilities=node.capabilities,
            status=self.derive_status(node.last_seen_at, now),
            last_seen_at=node.last_seen_at,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )
