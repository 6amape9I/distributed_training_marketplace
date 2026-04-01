from collections.abc import Sequence
from typing import Protocol

from orchestrator.app.domain.entities import Job
from orchestrator.app.domain.enums import OffchainJobStatus


class JobRepository(Protocol):
    def get(self, job_id: int) -> Job | None: ...

    def list(self) -> Sequence[Job]: ...

    def list_by_offchain_status(self, status: OffchainJobStatus) -> Sequence[Job]: ...

    def upsert(self, job: Job) -> Job: ...
