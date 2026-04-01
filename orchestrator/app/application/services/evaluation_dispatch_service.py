from __future__ import annotations

import json
from dataclasses import replace
from uuid import uuid4

from orchestrator.app.application.services.artifact_service import ArtifactService
from orchestrator.app.domain.entities import EvaluationTask
from orchestrator.app.domain.enums import (
    ArtifactKind,
    EvaluationTaskStatus,
    NodeRole,
    NodeStatus,
    OffchainJobStatus,
    TrainingTaskStatus,
)
from orchestrator.app.domain.repositories import EvaluationTaskRepository, JobRepository, NodeRepository, TrainingTaskRepository


_EVALUATION_SAMPLES = [
    {"features": [16.0, 12.0, 106.0, 820.0, 0.104], "label": 0},
    {"features": [17.4, 14.4, 112.0, 920.0, 0.098], "label": 0},
    {"features": [11.2, 18.0, 72.0, 360.0, 0.129], "label": 1},
    {"features": [12.8, 16.6, 83.0, 510.0, 0.112], "label": 1},
]


class EvaluationDispatchError(ValueError):
    pass


class EvaluationDispatchService:
    def __init__(
        self,
        jobs: JobRepository,
        nodes: NodeRepository,
        training_tasks: TrainingTaskRepository,
        evaluation_tasks: EvaluationTaskRepository,
        artifacts: ArtifactService,
    ) -> None:
        self.jobs = jobs
        self.nodes = nodes
        self.training_tasks = training_tasks
        self.evaluation_tasks = evaluation_tasks
        self.artifacts = artifacts

    def seed_for_job(self, job_id: int) -> tuple[list[EvaluationTask], list[str]]:
        job = self.jobs.get(job_id)
        if job is None:
            raise EvaluationDispatchError("job not found")
        if self.evaluation_tasks.list_by_job(job_id):
            raise EvaluationDispatchError("evaluation tasks already exist for job")

        job_training_tasks = list(self.training_tasks.list_by_job(job_id))
        completed_training_tasks = [task for task in job_training_tasks if task.status == TrainingTaskStatus.COMPLETED]
        if not completed_training_tasks:
            raise EvaluationDispatchError("no completed training tasks available")
        if any(
            task.status in {TrainingTaskStatus.PENDING, TrainingTaskStatus.CLAIMED, TrainingTaskStatus.RUNNING}
            for task in job_training_tasks
        ):
            raise EvaluationDispatchError("training tasks are still in progress")

        evaluators = [node for node in self.nodes.list_by_role(NodeRole.EVALUATOR) if node.status == NodeStatus.ONLINE]
        if not evaluators:
            raise EvaluationDispatchError("no online evaluator nodes available")

        feature_count = len(_EVALUATION_SAMPLES[0]["features"])
        manifest_artifact = self.artifacts.upload(
            kind=ArtifactKind.EVALUATION_INPUT_MANIFEST,
            name=f"job-{job_id}-evaluation-manifest.json",
            payload=json.dumps(
                {
                    "partition_id": f"job-{job_id}-evaluation",
                    "feature_count": feature_count,
                    "samples": _EVALUATION_SAMPLES,
                },
                sort_keys=True,
            ).encode("utf-8"),
            mime_type="application/json",
            metadata={"job_id": job_id, "purpose": "evaluation"},
            job_id=job_id,
        )

        created: list[EvaluationTask] = []
        artifact_ids = [manifest_artifact.artifact_id]
        for task in completed_training_tasks:
            created.append(
                self.evaluation_tasks.upsert(
                    EvaluationTask(
                        evaluation_task_id=f"evaluation-task-{uuid4().hex}",
                        job_id=job_id,
                        source_training_task_id=task.task_id,
                        evaluator_node_id=None,
                        status=EvaluationTaskStatus.PENDING,
                        target_model_artifact_uri=task.result_artifact_uri or "",
                        dataset_artifact_uri=manifest_artifact.uri,
                        config_json={"accuracy_threshold": 0.75, "feature_count": feature_count},
                    )
                )
            )

        self.jobs.upsert(replace(job, offchain_status=OffchainJobStatus.EVALUATING))
        return created, artifact_ids
