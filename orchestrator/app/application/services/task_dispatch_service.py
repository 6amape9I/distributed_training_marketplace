from __future__ import annotations

import json
from uuid import uuid4

from orchestrator.app.application.services.artifact_service import ArtifactService
from orchestrator.app.domain.entities import TrainingTask
from orchestrator.app.domain.enums import ArtifactKind, NodeRole, NodeStatus, TrainingTaskStatus, TrainingTaskType
from orchestrator.app.domain.repositories import JobRepository, NodeRepository, TrainingTaskRepository


_DEMO_SAMPLES = [
    {"features": [18.0, 10.4, 122.8, 1001.0, 0.1184], "label": 0},
    {"features": [20.6, 17.8, 132.9, 1326.0, 0.0847], "label": 0},
    {"features": [19.7, 21.2, 130.0, 1203.0, 0.1096], "label": 0},
    {"features": [11.4, 20.4, 77.6, 386.1, 0.1425], "label": 1},
    {"features": [12.4, 15.7, 82.6, 477.1, 0.1278], "label": 1},
    {"features": [13.1, 15.7, 85.6, 516.0, 0.1078], "label": 1},
    {"features": [14.2, 20.0, 92.4, 618.4, 0.0893], "label": 1},
    {"features": [15.2, 13.8, 98.7, 716.9, 0.0904], "label": 0},
    {"features": [13.7, 20.8, 90.2, 577.9, 0.1189], "label": 1},
    {"features": [12.1, 13.0, 78.8, 462.0, 0.0811], "label": 1},
    {"features": [17.9, 10.4, 122.0, 999.1, 0.1180], "label": 0},
    {"features": [18.2, 18.0, 119.6, 1040.1, 0.0946], "label": 0},
]


class TaskDispatchError(ValueError):
    pass


class TaskDispatchService:
    def __init__(
        self,
        jobs: JobRepository,
        nodes: NodeRepository,
        tasks: TrainingTaskRepository,
        artifacts: ArtifactService,
    ) -> None:
        self.jobs = jobs
        self.nodes = nodes
        self.tasks = tasks
        self.artifacts = artifacts

    def seed_demo_tasks_for_job(self, job_id: int) -> tuple[list[TrainingTask], list[str]]:
        job = self.jobs.get(job_id)
        if job is None:
            raise TaskDispatchError("job not found")
        if self.tasks.list_by_job(job_id):
            raise TaskDispatchError("tasks already exist for job")

        trainers = [
            node for node in self.nodes.list_by_role(NodeRole.TRAINER) if node.status == NodeStatus.ONLINE
        ]
        if not trainers:
            raise TaskDispatchError("no online trainer nodes available")

        feature_count = len(_DEMO_SAMPLES[0]["features"])
        model_artifact = self.artifacts.upload(
            kind=ArtifactKind.MODEL_INPUT,
            name=f"job-{job_id}-initial-model.json",
            payload=json.dumps({"weights": [0.0] * feature_count, "bias": 0.0}, sort_keys=True).encode("utf-8"),
            mime_type="application/json",
            metadata={"job_id": job_id, "feature_count": feature_count},
            job_id=job_id,
        )

        partitions = self._partition_samples(len(trainers))
        created_tasks: list[TrainingTask] = []
        artifact_ids = [model_artifact.artifact_id]
        for index, trainer in enumerate(trainers):
            partition_id = f"job-{job_id}-partition-{index + 1}"
            dataset_artifact = self.artifacts.upload(
                kind=ArtifactKind.DATASET_MANIFEST,
                name=f"{partition_id}.json",
                payload=json.dumps(
                    {
                        "partition_id": partition_id,
                        "feature_count": feature_count,
                        "samples": partitions[index],
                    },
                    sort_keys=True,
                ).encode("utf-8"),
                mime_type="application/json",
                metadata={"job_id": job_id, "trainer_hint": trainer.node_id},
                job_id=job_id,
            )
            artifact_ids.append(dataset_artifact.artifact_id)
            task = TrainingTask(
                task_id=f"task-{uuid4().hex}",
                job_id=job_id,
                trainer_node_id=None,
                task_type=TrainingTaskType.LOCAL_FIT,
                status=TrainingTaskStatus.PENDING,
                data_partition_id=partition_id,
                model_artifact_uri=model_artifact.uri,
                dataset_artifact_uri=dataset_artifact.uri,
                config_json={"epochs": 12, "learning_rate": 0.5, "feature_count": feature_count},
            )
            created_tasks.append(self.tasks.upsert(task))
        return created_tasks, artifact_ids

    def _partition_samples(self, partition_count: int) -> list[list[dict[str, object]]]:
        partitions = [[] for _ in range(partition_count)]
        for index, sample in enumerate(_DEMO_SAMPLES):
            partitions[index % partition_count].append(sample)
        return partitions
