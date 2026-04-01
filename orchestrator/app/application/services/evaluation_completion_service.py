from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from orchestrator.app.domain.entities import EvaluationReport, EvaluationTask
from orchestrator.app.domain.enums import EvaluationTaskStatus, OffchainJobStatus
from orchestrator.app.domain.repositories import (
    ArtifactRepository,
    EvaluationReportRepository,
    EvaluationTaskRepository,
    JobRepository,
)


class EvaluationCompletionError(ValueError):
    pass


class EvaluationCompletionService:
    def __init__(
        self,
        tasks: EvaluationTaskRepository,
        artifacts: ArtifactRepository,
        reports: EvaluationReportRepository,
        jobs: JobRepository,
    ) -> None:
        self.tasks = tasks
        self.artifacts = artifacts
        self.reports = reports
        self.jobs = jobs

    def get(self, evaluation_task_id: str) -> EvaluationTask | None:
        return self.tasks.get(evaluation_task_id)

    def start(self, evaluation_task_id: str, evaluator_node_id: str) -> EvaluationTask:
        task = self._owned_task(evaluation_task_id, evaluator_node_id)
        if task.status not in {EvaluationTaskStatus.CLAIMED, EvaluationTaskStatus.RUNNING}:
            raise EvaluationCompletionError("evaluation task is not claimable for start")
        started = replace(task, status=EvaluationTaskStatus.RUNNING)
        return self.tasks.upsert(started)

    def complete(
        self,
        evaluation_task_id: str,
        evaluator_node_id: str,
        report_artifact_id: str,
        metrics_json: dict[str, float | int | bool | str],
        sample_count: int,
        acceptance_decision: bool,
        target_model_digest: str,
    ) -> EvaluationTask:
        task = self._owned_task(evaluation_task_id, evaluator_node_id)
        if task.status not in {EvaluationTaskStatus.CLAIMED, EvaluationTaskStatus.RUNNING}:
            raise EvaluationCompletionError("evaluation task cannot be completed from its current status")
        report_artifact = self.artifacts.get(report_artifact_id)
        if report_artifact is None:
            raise EvaluationCompletionError("evaluation report artifact not found")
        if report_artifact.task_id not in {None, task.evaluation_task_id}:
            raise EvaluationCompletionError("report artifact does not belong to evaluation task")
        self.reports.upsert(
            EvaluationReport(
                report_id=f"evaluation-report-{uuid4().hex}",
                evaluation_task_id=task.evaluation_task_id,
                job_id=task.job_id,
                source_training_task_id=task.source_training_task_id,
                evaluator_node_id=evaluator_node_id,
                metrics_json=metrics_json,
                sample_count=sample_count,
                acceptance_decision=acceptance_decision,
                target_model_digest=target_model_digest,
            )
        )
        completed = replace(
            task,
            status=EvaluationTaskStatus.COMPLETED,
            report_artifact_uri=report_artifact.uri,
            report_artifact_hash=report_artifact.content_hash,
            completed_at=datetime.now(timezone.utc),
            failure_reason=None,
        )
        saved = self.tasks.upsert(completed)
        self._reconcile_job_status(task.job_id)
        return saved

    def fail(self, evaluation_task_id: str, evaluator_node_id: str, failure_reason: str) -> EvaluationTask:
        task = self._owned_task(evaluation_task_id, evaluator_node_id)
        if task.status in {EvaluationTaskStatus.COMPLETED, EvaluationTaskStatus.CANCELLED}:
            raise EvaluationCompletionError("evaluation task can no longer fail")
        failed = replace(
            task,
            status=EvaluationTaskStatus.FAILED,
            completed_at=datetime.now(timezone.utc),
            failure_reason=failure_reason,
        )
        saved = self.tasks.upsert(failed)
        self._reconcile_job_status(task.job_id)
        return saved

    def _reconcile_job_status(self, job_id: int) -> None:
        job = self.jobs.get(job_id)
        if job is None:
            raise EvaluationCompletionError("job not found for evaluation reconciliation")
        tasks = list(self.tasks.list_by_job(job_id))
        if not tasks:
            return
        if any(task.status in {EvaluationTaskStatus.PENDING, EvaluationTaskStatus.CLAIMED, EvaluationTaskStatus.RUNNING} for task in tasks):
            if job.offchain_status != OffchainJobStatus.EVALUATING:
                self.jobs.upsert(replace(job, offchain_status=OffchainJobStatus.EVALUATING))
            return
        if any(task.status == EvaluationTaskStatus.FAILED for task in tasks):
            self.jobs.upsert(replace(job, offchain_status=OffchainJobStatus.EVALUATION_FAILED))
            return
        reports = list(self.reports.list_by_job(job_id))
        if len(reports) < len(tasks):
            self.jobs.upsert(replace(job, offchain_status=OffchainJobStatus.EVALUATION_FAILED))
            return
        accepted = all(report.acceptance_decision for report in reports)
        self.jobs.upsert(
            replace(
                job,
                offchain_status=OffchainJobStatus.READY_FOR_ATTESTATION if accepted else OffchainJobStatus.EVALUATION_FAILED,
            )
        )

    def _owned_task(self, evaluation_task_id: str, evaluator_node_id: str) -> EvaluationTask:
        task = self.tasks.get(evaluation_task_id)
        if task is None:
            raise EvaluationCompletionError("evaluation task not found")
        if task.evaluator_node_id != evaluator_node_id:
            raise EvaluationCompletionError("evaluation task is not owned by this evaluator")
        return task
