from pydantic import BaseModel, Field

from shared.python.enums import JobStatus


class ArtifactRef(BaseModel):
    uri: str
    digest: str | None = None


class SettlementDecision(BaseModel):
    provider_payout_wei: int = Field(ge=0)
    requester_refund_wei: int = Field(ge=0)
    settlement_hash: str


class JobRecord(BaseModel):
    job_id: int
    requester: str
    provider: str
    attestor: str
    status: JobStatus
    artifact: ArtifactRef | None = None
