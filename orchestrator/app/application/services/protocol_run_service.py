from __future__ import annotations

from dataclasses import replace

from orchestrator.app.application.protocol_runtime.fedavg_like_v1 import ProtocolRunError
from orchestrator.app.application.protocol_runtime.registry import ProtocolRegistry
from orchestrator.app.application.protocol_runtime.types import ProtocolRunResult
from orchestrator.app.domain.enums import OffchainJobStatus
from orchestrator.app.domain.repositories import JobRepository


class ProtocolRunService:
    def __init__(self, jobs: JobRepository, protocols: ProtocolRegistry, default_protocol_name: str = "fedavg_like_v1") -> None:
        self.jobs = jobs
        self.protocols = protocols
        self.default_protocol_name = default_protocol_name

    def start_for_job(self, job_id: int) -> ProtocolRunResult:
        job = self.jobs.get(job_id)
        if job is None:
            raise ProtocolRunError("job not found")
        if job.offchain_status != OffchainJobStatus.SCHEDULING:
            raise ProtocolRunError("job is not ready for protocol execution")
        protocol = self.protocols.get(self.default_protocol_name)
        return protocol.start_run_for_job(job_id)

    def mark_job_evaluating(self, job_id: int) -> None:
        job = self.jobs.get(job_id)
        if job is None:
            raise ProtocolRunError("job not found")
        if job.offchain_status != OffchainJobStatus.EVALUATING:
            self.jobs.upsert(replace(job, offchain_status=OffchainJobStatus.EVALUATING))
