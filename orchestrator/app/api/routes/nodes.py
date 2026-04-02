from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from orchestrator.app.api.deps import get_container, get_db_session, get_node_liveness_service, get_node_registry_service
from orchestrator.app.application.dto import NodeHeartbeatRequest, NodeRegistrationRequest, NodeResponse
from orchestrator.app.application.services import NodeLivenessService, NodeRegistryService
from orchestrator.app.domain.enums import NodeRole
from orchestrator.app.infrastructure.container import AppContainer

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("", response_model=list[NodeResponse])
def list_nodes(
    session: Annotated[Session, Depends(get_db_session)],
    container: Annotated[AppContainer, Depends(get_container)],
    liveness: Annotated[NodeLivenessService, Depends(get_node_liveness_service)],
) -> list[NodeResponse]:
    nodes = [liveness.refresh(node, datetime.now(timezone.utc)) for node in container.node_repository(session).list()]
    return [
        NodeResponse(
            node_id=node.node_id,
            role=node.role.value,
            endpoint_url=node.endpoint_url,
            capabilities=node.capabilities,
            status=node.status.value,
            last_seen_at=node.last_seen_at,
            updated_at=node.updated_at,
        )
        for node in nodes
    ]


@router.get("/{node_id}", response_model=NodeResponse)
def get_node(
    node_id: str,
    session: Annotated[Session, Depends(get_db_session)],
    container: Annotated[AppContainer, Depends(get_container)],
    liveness: Annotated[NodeLivenessService, Depends(get_node_liveness_service)],
) -> NodeResponse:
    node = container.node_repository(session).get(node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node not found")
    refreshed = liveness.refresh(node, datetime.now(timezone.utc))
    return NodeResponse(
        node_id=refreshed.node_id,
        role=refreshed.role.value,
        endpoint_url=refreshed.endpoint_url,
        capabilities=refreshed.capabilities,
        status=refreshed.status.value,
        last_seen_at=refreshed.last_seen_at,
        updated_at=refreshed.updated_at,
    )


@router.post("/register", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def register_node(
    payload: NodeRegistrationRequest,
    service: Annotated[NodeRegistryService, Depends(get_node_registry_service)],
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> NodeResponse:
    node = service.register(
        node_id=payload.node_id,
        role=payload.role,
        endpoint_url=str(payload.endpoint_url),
        capabilities=payload.capabilities,
    )
    if session is not None:
        session.commit()
    return NodeResponse(
        node_id=node.node_id,
        role=node.role.value,
        endpoint_url=node.endpoint_url,
        capabilities=node.capabilities,
        status=node.status.value,
        last_seen_at=node.last_seen_at,
        updated_at=node.updated_at,
    )


@router.post("/heartbeat", response_model=NodeResponse)
def heartbeat_node(
    payload: NodeHeartbeatRequest,
    service: Annotated[NodeRegistryService, Depends(get_node_registry_service)],
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> NodeResponse:
    node = service.heartbeat(payload.node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node not found")
    if session is not None:
        session.commit()
    return NodeResponse(
        node_id=node.node_id,
        role=node.role.value,
        endpoint_url=node.endpoint_url,
        capabilities=node.capabilities,
        status=node.status.value,
        last_seen_at=node.last_seen_at,
        updated_at=node.updated_at,
    )
