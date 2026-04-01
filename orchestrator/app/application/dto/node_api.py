from datetime import datetime
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, Field

from orchestrator.app.domain.enums import NodeRole


class NodeRegistrationRequest(BaseModel):
    node_id: str = Field(min_length=1, max_length=128)
    role: NodeRole
    endpoint_url: AnyHttpUrl
    capabilities: dict[str, Any] | None = None


class NodeHeartbeatRequest(BaseModel):
    node_id: str = Field(min_length=1, max_length=128)


class NodeResponse(BaseModel):
    node_id: str
    role: str
    endpoint_url: str
    capabilities: dict[str, Any] | None = None
    status: str
    last_seen_at: datetime | None = None
    updated_at: datetime | None = None
