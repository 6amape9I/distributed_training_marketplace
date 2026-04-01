from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestrator.app.domain.enums import NodeRole, NodeStatus


@dataclass(slots=True, frozen=True)
class Node:
    node_id: str
    role: NodeRole
    endpoint_url: str
    capabilities: dict[str, Any] | None
    status: NodeStatus
    last_seen_at: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
