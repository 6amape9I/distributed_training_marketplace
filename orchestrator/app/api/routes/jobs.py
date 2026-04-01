from fastapi import APIRouter

from orchestrator.app.application.dto.job_summary import JobSummary
from shared.python.enums import JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobSummary])
def list_jobs() -> list[JobSummary]:
    return [JobSummary(job_id=0, status=JobStatus.OPEN, settlement_ready=False)]
