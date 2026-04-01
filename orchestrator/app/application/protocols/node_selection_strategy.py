from collections.abc import Sequence
from typing import Protocol

from shared.python.ids import JobId


class NodeSelectionStrategy(Protocol):
    def select(self, job_id: JobId, candidate_nodes: Sequence[str]) -> list[str]: ...
