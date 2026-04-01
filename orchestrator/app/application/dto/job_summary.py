from pydantic import BaseModel

from shared.python.enums import JobStatus


class JobSummary(BaseModel):
    job_id: int
    status: JobStatus
    settlement_ready: bool
