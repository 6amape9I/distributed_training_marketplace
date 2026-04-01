from pydantic import BaseModel


class NodeSummary(BaseModel):
    node_id: str
    role: str
    state: str
