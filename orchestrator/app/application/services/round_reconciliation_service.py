from __future__ import annotations

from dataclasses import replace

from orchestrator.app.application.protocol_runtime.fedavg_like_v1 import AggregationError
from orchestrator.app.application.protocol_runtime.registry import ProtocolRegistry
from orchestrator.app.domain.entities import Round
from orchestrator.app.domain.enums import EvaluationTaskStatus, OffchainJobStatus, RoundStatus, TrainingTaskStatus
from orchestrator.app.domain.repositories import EvaluationReportRepository, EvaluationTaskRepository, JobRepository, RoundRepository, TrainingTaskRepository


class RoundReconciliationError(ValueError):
    pass


class RoundReconciliationService:
    def __init__(
        self,
        *,
        rounds: RoundRepository,
        jobs: JobRepository,
        training_tasks: TrainingTaskRepository,
        evaluation_tasks: EvaluationTaskRepository,
        evaluation_reports: EvaluationReportRepository,
        protocols: ProtocolRegistry,
    ) -> None:
        self.rounds = rounds
        self.jobs = jobs
        self.training_tasks = training_tasks
        self.evaluation_tasks = evaluation_tasks
        self.evaluation_reports = evaluation_reports
        self.protocols = protocols

    def get(self, round_id: str) -> Round | None:
        return self.rounds.get(round_id)

    def list_by_job(self, job_id: int) -> list[Round]:
        return list(self.rounds.list_by_job(job_id))

    def reconcile(self, round_id: str) -> Round:
        round_record = self.rounds.get(round_id)
        if round_record is None:
            raise RoundReconciliationError("round not found")

        if round_record.status in {RoundStatus.PENDING, RoundStatus.SEEDED, RoundStatus.TRAINING}:
            return self._reconcile_training(round_record)
        if round_record.status in {RoundStatus.AGGREGATING, RoundStatus.EVALUATING}:
            return self._reconcile_evaluation(round_record)
        return round_record

    def _reconcile_training(self, round_record: Round) -> Round:
        tasks = list(self.training_tasks.list_by_round(round_record.round_id))
        if not tasks:
            raise RoundReconciliationError("round has no training tasks")
        if any(task.status == TrainingTaskStatus.FAILED for task in tasks):
            return self._fail_round(round_record, OffchainJobStatus.FAILED, "trainer task failed")
        if any(task.status != TrainingTaskStatus.COMPLETED for task in tasks):
            if round_record.status != RoundStatus.TRAINING:
                return self.rounds.upsert(replace(round_record, status=RoundStatus.TRAINING))
            return round_record
        protocol = self.protocols.get(round_record.protocol_name)
        try:
            aggregation = protocol.aggregate_round(round_record)
            seeded = protocol.seed_evaluation(aggregation.round_record)
        except AggregationError as exc:
            return self._fail_round(round_record, OffchainJobStatus.FAILED, str(exc))
        except ValueError as exc:
            return self._fail_round(round_record, OffchainJobStatus.FAILED, str(exc))
        job = self.jobs.get(round_record.job_id)
        if job is not None and job.offchain_status != OffchainJobStatus.EVALUATING:
            self.jobs.upsert(replace(job, offchain_status=OffchainJobStatus.EVALUATING))
        return seeded.round_record

    def _reconcile_evaluation(self, round_record: Round) -> Round:
        tasks = list(self.evaluation_tasks.list_by_round(round_record.round_id))
        if not tasks:
            raise RoundReconciliationError("round has no evaluation tasks")
        if any(task.status in {EvaluationTaskStatus.PENDING, EvaluationTaskStatus.CLAIMED, EvaluationTaskStatus.RUNNING} for task in tasks):
            if round_record.status != RoundStatus.EVALUATING:
                return self.rounds.upsert(replace(round_record, status=RoundStatus.EVALUATING))
            return round_record
        if any(task.status == EvaluationTaskStatus.FAILED for task in tasks):
            return self._fail_round(round_record, OffchainJobStatus.EVALUATION_FAILED, "evaluation task failed")
        reports = list(self.evaluation_reports.list_by_round(round_record.round_id))
        if len(reports) != len(tasks):
            return self._fail_round(round_record, OffchainJobStatus.FAILED, "evaluation report mismatch")
        accepted = all(report.acceptance_decision for report in reports)
        job = self.jobs.get(round_record.job_id)
        if job is None:
            raise RoundReconciliationError("job not found")
        if accepted:
            self.jobs.upsert(replace(job, offchain_status=OffchainJobStatus.READY_FOR_ATTESTATION))
            return self.rounds.upsert(replace(round_record, status=RoundStatus.COMPLETED, evaluation_report_id=reports[0].report_id))
        self.jobs.upsert(replace(job, offchain_status=OffchainJobStatus.EVALUATION_FAILED))
        return self.rounds.upsert(
            replace(
                round_record,
                status=RoundStatus.FAILED,
                evaluation_report_id=reports[0].report_id,
                failure_reason="evaluation rejected aggregated model",
            )
        )

    def _fail_round(self, round_record: Round, job_status: OffchainJobStatus, reason: str) -> Round:
        job = self.jobs.get(round_record.job_id)
        if job is None:
            raise RoundReconciliationError("job not found")
        self.jobs.upsert(replace(job, offchain_status=job_status))
        return self.rounds.upsert(replace(round_record, status=RoundStatus.FAILED, failure_reason=reason))
