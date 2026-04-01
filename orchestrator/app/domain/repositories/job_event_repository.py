from typing import Protocol

from orchestrator.app.domain.entities import JobEventRecord


class JobEventRepository(Protocol):
    def exists(self, transaction_hash: str, log_index: int) -> bool: ...

    def add(self, event: JobEventRecord) -> JobEventRecord: ...
