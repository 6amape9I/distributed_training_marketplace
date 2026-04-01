from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from orchestrator.app.domain.entities import TrainingTask
from orchestrator.app.domain.enums import TrainingTaskStatus
from orchestrator.app.domain.repositories import ArtifactRepository, TrainingTaskRepository


class TaskCompletionError(ValueError):
    pass


class TaskCompletionService:
    def __init__(self, tasks: TrainingTaskRepository, artifacts: ArtifactRepository) -> None:
        self.tasks = tasks
        self.artifacts = artifacts

    def get(self, task_id: str) -> TrainingTask | None:
        return self.tasks.get(task_id)

    def start(self, task_id: str, trainer_node_id: str) -> TrainingTask:
        task = self._owned_task(task_id, trainer_node_id)
        if task.status not in {TrainingTaskStatus.CLAIMED, TrainingTaskStatus.RUNNING}:
            raise TaskCompletionError("task is not claimable for start")
        started = replace(task, status=TrainingTaskStatus.RUNNING)
        return self.tasks.upsert(started)

    def complete(self, task_id: str, trainer_node_id: str, result_artifact_id: str, report_artifact_id: str) -> TrainingTask:
        task = self._owned_task(task_id, trainer_node_id)
        if task.status not in {TrainingTaskStatus.CLAIMED, TrainingTaskStatus.RUNNING}:
            raise TaskCompletionError("task cannot be completed from its current status")
        result_artifact = self.artifacts.get(result_artifact_id)
        report_artifact = self.artifacts.get(report_artifact_id)
        if result_artifact is None or report_artifact is None:
            raise TaskCompletionError("result or report artifact not found")
        if result_artifact.task_id not in {None, task.task_id} or report_artifact.task_id not in {None, task.task_id}:
            raise TaskCompletionError("artifact does not belong to task")
        completed = replace(
            task,
            status=TrainingTaskStatus.COMPLETED,
            result_artifact_uri=result_artifact.uri,
            result_artifact_hash=result_artifact.content_hash,
            report_artifact_uri=report_artifact.uri,
            report_artifact_hash=report_artifact.content_hash,
            completed_at=datetime.now(timezone.utc),
            failure_reason=None,
        )
        return self.tasks.upsert(completed)

    def fail(self, task_id: str, trainer_node_id: str, failure_reason: str) -> TrainingTask:
        task = self._owned_task(task_id, trainer_node_id)
        if task.status in {TrainingTaskStatus.COMPLETED, TrainingTaskStatus.CANCELLED}:
            raise TaskCompletionError("task can no longer fail")
        failed = replace(
            task,
            status=TrainingTaskStatus.FAILED,
            completed_at=datetime.now(timezone.utc),
            failure_reason=failure_reason,
        )
        return self.tasks.upsert(failed)

    def _owned_task(self, task_id: str, trainer_node_id: str) -> TrainingTask:
        task = self.tasks.get(task_id)
        if task is None:
            raise TaskCompletionError("task not found")
        if task.trainer_node_id != trainer_node_id:
            raise TaskCompletionError("task is not owned by this trainer")
        return task
