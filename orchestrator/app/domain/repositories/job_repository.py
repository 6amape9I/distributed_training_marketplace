from typing import Protocol

from orchestrator.app.domain.entities.job import Job
from shared.python.ids import JobId


class JobRepository(Protocol):
    def get(self, job_id: JobId) -> Job | None: ...
