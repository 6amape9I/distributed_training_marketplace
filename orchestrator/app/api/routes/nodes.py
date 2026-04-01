from fastapi import APIRouter

from orchestrator.app.application.dto.node_summary import NodeSummary

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("", response_model=list[NodeSummary])
def list_nodes() -> list[NodeSummary]:
    return [NodeSummary(node_id="stage1-node", role="trainer", state="placeholder")]
