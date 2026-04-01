from collections.abc import Sequence
from typing import Protocol

from orchestrator.app.domain.entities import Node
from orchestrator.app.domain.enums import NodeRole


class NodeRepository(Protocol):
    def get(self, node_id: str) -> Node | None: ...

    def list(self) -> Sequence[Node]: ...

    def list_by_role(self, role: NodeRole) -> Sequence[Node]: ...

    def upsert(self, node: Node) -> Node: ...
