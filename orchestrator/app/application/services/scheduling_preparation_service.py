from __future__ import annotations

from orchestrator.app.domain.entities import Job
from orchestrator.app.domain.enums import NodeRole, OffchainJobStatus
from orchestrator.app.domain.repositories import JobRepository, NodeRepository
from shared.python.ids import JobId

from .job_lifecycle_service import JobLifecycleService
from .simple_node_selection_strategy import SimpleNodeSelectionStrategy


class SchedulingPreparationService:
    def __init__(
        self,
        *,
        jobs: JobRepository,
        nodes: NodeRepository,
        lifecycle: JobLifecycleService,
        node_selection: SimpleNodeSelectionStrategy,
    ) -> None:
        self.jobs = jobs
        self.nodes = nodes
        self.lifecycle = lifecycle
        self.node_selection = node_selection

    def reconcile(self) -> int:
        changed = 0
        trainer_ids = [node.node_id for node in self.nodes.list_by_role(NodeRole.TRAINER) if node.status.value == "online"]
        evaluator_ids = [node.node_id for node in self.nodes.list_by_role(NodeRole.EVALUATOR) if node.status.value == "online"]
        funded_jobs = list(self.jobs.list_by_offchain_status(OffchainJobStatus.FUNDED))
        ready_jobs = list(self.jobs.list_by_offchain_status(OffchainJobStatus.READY_FOR_SCHEDULING))

        for job in funded_jobs:
            selected = self.node_selection.select(JobId(job.job_id), trainer_ids)
            next_status = self.lifecycle.prepare_for_scheduling(
                job.offchain_status,
                has_trainers=bool(selected),
                has_evaluator=bool(evaluator_ids),
            )
            if next_status != job.offchain_status:
                self.jobs.upsert(_replace_job_status(job, next_status))
                changed += 1

        for job in ready_jobs:
            selected = self.node_selection.select(JobId(job.job_id), trainer_ids)
            next_status = self.lifecycle.prepare_for_scheduling(
                job.offchain_status,
                has_trainers=bool(selected),
                has_evaluator=bool(evaluator_ids),
            )
            if next_status != job.offchain_status:
                self.jobs.upsert(_replace_job_status(job, next_status))
                changed += 1

        return changed


def _replace_job_status(job: Job, next_status: OffchainJobStatus) -> Job:
    return Job(
        job_id=job.job_id,
        requester=job.requester,
        provider=job.provider,
        attestor=job.attestor,
        target_escrow_wei=job.target_escrow_wei,
        escrow_balance_wei=job.escrow_balance_wei,
        job_spec_hash=job.job_spec_hash,
        onchain_status=job.onchain_status,
        offchain_status=next_status,
        attestation_hash=job.attestation_hash,
        settlement_hash=job.settlement_hash,
        provider_payout_wei=job.provider_payout_wei,
        requester_refund_wei=job.requester_refund_wei,
        last_chain_block=job.last_chain_block,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
