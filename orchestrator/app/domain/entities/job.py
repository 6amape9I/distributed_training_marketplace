from dataclasses import dataclass

from shared.python.enums import JobStatus
from shared.python.ids import JobId


@dataclass(slots=True, frozen=True)
class Job:
    job_id: JobId
    requester: str
    provider: str
    attestor: str
    status: JobStatus
    escrow_wei: int
