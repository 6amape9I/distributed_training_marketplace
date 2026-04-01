from collections.abc import Sequence

from shared.python.ids import JobId


class SimpleNodeSelectionStrategy:
    def select(self, job_id: JobId, candidate_nodes: Sequence[str]) -> list[str]:
        _ = job_id
        return sorted(candidate_nodes)
