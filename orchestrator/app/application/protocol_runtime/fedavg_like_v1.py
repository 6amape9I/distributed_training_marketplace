from __future__ import annotations

import json
from dataclasses import replace
from uuid import uuid4

from orchestrator.app.application.protocol_runtime.types import AggregationResult, EvaluationSeedResult, ProtocolRunResult, RoundPlan
from orchestrator.app.application.services.fedavg_like_aggregation_service import (
    FedAvgLikeAggregationError,
    FedAvgLikeAggregationService,
)
from orchestrator.app.application.services.artifact_service import ArtifactService
from orchestrator.app.application.services.evaluation_dispatch_service import EvaluationDispatchError
from orchestrator.app.domain.entities import EvaluationTask, Job, Node, Round, TrainingTask
from orchestrator.app.domain.enums import ArtifactKind, EvaluationTaskStatus, NodeRole, NodeStatus, RoundStatus, TrainingTaskStatus, TrainingTaskType
from orchestrator.app.domain.repositories import EvaluationTaskRepository, JobRepository, NodeRepository, RoundRepository, TrainingTaskRepository

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

_EVALUATION_SAMPLES = [
    {"features": [16.0, 12.0, 106.0, 820.0, 0.104], "label": 0},
    {"features": [17.4, 14.4, 112.0, 920.0, 0.098], "label": 0},
    {"features": [11.2, 18.0, 72.0, 360.0, 0.129], "label": 1},
    {"features": [12.8, 16.6, 83.0, 510.0, 0.112], "label": 1},
]


class ProtocolRunError(ValueError):
    pass


class AggregationError(ValueError):
    pass


class FedAvgLikeV1Protocol:
    protocol_name = "fedavg_like_v1"

    def __init__(
        self,
        *,
        jobs: JobRepository,
        nodes: NodeRepository,
        rounds: RoundRepository,
        training_tasks: TrainingTaskRepository,
        evaluation_tasks: EvaluationTaskRepository,
        artifacts: ArtifactService,
        aggregation: FedAvgLikeAggregationService,
    ) -> None:
        self.jobs = jobs
        self.nodes = nodes
        self.rounds = rounds
        self.training_tasks = training_tasks
        self.evaluation_tasks = evaluation_tasks
        self.artifacts = artifacts
        self.aggregation = aggregation

    def start_run_for_job(self, job_id: int) -> ProtocolRunResult:
        job = self._require_job(job_id)
        active = self.rounds.get_active_for_job(job_id)
        if active is not None:
            raise ProtocolRunError("active round already exists for job")

        trainers = [node for node in self.nodes.list_by_role(NodeRole.TRAINER) if node.status == NodeStatus.ONLINE]
        evaluators = [node for node in self.nodes.list_by_role(NodeRole.EVALUATOR) if node.status == NodeStatus.ONLINE]
        if not trainers:
            raise ProtocolRunError("no online trainer nodes available")
        if not evaluators:
            raise ProtocolRunError("no online evaluator nodes available")

        round_record = self.rounds.upsert(
            Round(
                round_id=f"round-{uuid4().hex}",
                job_id=job_id,
                protocol_name=self.protocol_name,
                round_index=1,
                status=RoundStatus.PENDING,
                base_model_artifact_uri="",
            )
        )
        plan = self.prepare_round(job, round_record, len(trainers))
        tasks = self.seed_training_tasks(plan.round_record, trainers)
        current_round = self.rounds.get(plan.round_record.round_id) or plan.round_record
        return ProtocolRunResult(round_record=current_round, training_tasks=tasks, artifact_ids=plan.artifact_ids)

    def prepare_round(self, job: Job, round_record: Round, trainer_count: int) -> RoundPlan:
        feature_count = len(_DEMO_SAMPLES[0]["features"])
        model_artifact = self.artifacts.upload(
            kind=ArtifactKind.MODEL_INPUT,
            name=f"job-{job.job_id}-round-{round_record.round_index}-base-model.json",
            payload=json.dumps({"weights": [0.0] * feature_count, "bias": 0.0}, sort_keys=True).encode("utf-8"),
            mime_type="application/json",
            metadata={"job_id": job.job_id, "round_id": round_record.round_id, "feature_count": feature_count},
            job_id=job.job_id,
        )
        prepared_round = self.rounds.upsert(
            replace(round_record, status=RoundStatus.SEEDED, base_model_artifact_uri=model_artifact.uri)
        )
        return RoundPlan(round_record=prepared_round, task_count=trainer_count, artifact_ids=[model_artifact.artifact_id])

    def seed_training_tasks(self, round_record: Round, trainers: list[Node]) -> list[TrainingTask]:
        if round_record.status not in {RoundStatus.PENDING, RoundStatus.SEEDED}:
            raise ProtocolRunError("round is not ready for training task seeding")
        if self.training_tasks.list_by_round(round_record.round_id):
            raise ProtocolRunError("round training tasks already exist")

        feature_count = len(_DEMO_SAMPLES[0]["features"])
        partitions = self._partition_samples(len(trainers))
        created_tasks: list[TrainingTask] = []
        for index, trainer in enumerate(trainers):
            partition_id = f"job-{round_record.job_id}-round-{round_record.round_index}-partition-{index + 1}"
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
                metadata={
                    "job_id": round_record.job_id,
                    "round_id": round_record.round_id,
                    "trainer_hint": trainer.node_id,
                },
                job_id=round_record.job_id,
            )
            task = TrainingTask(
                task_id=f"task-{uuid4().hex}",
                job_id=round_record.job_id,
                round_id=round_record.round_id,
                trainer_node_id=None,
                task_type=TrainingTaskType.LOCAL_FIT,
                status=TrainingTaskStatus.PENDING,
                data_partition_id=partition_id,
                model_artifact_uri=round_record.base_model_artifact_uri,
                dataset_artifact_uri=dataset_artifact.uri,
                config_json={"epochs": 12, "learning_rate": 0.5, "feature_count": feature_count},
            )
            created_tasks.append(self.training_tasks.upsert(task))
        self.rounds.upsert(replace(round_record, status=RoundStatus.TRAINING))
        return created_tasks

    def aggregate_round(self, round_record: Round) -> AggregationResult:
        tasks = list(self.training_tasks.list_by_round(round_record.round_id))
        if not tasks:
            raise AggregationError("round has no training tasks")
        if any(task.status == TrainingTaskStatus.FAILED for task in tasks):
            raise AggregationError("round contains failed trainer task")
        if any(task.status != TrainingTaskStatus.COMPLETED for task in tasks):
            raise AggregationError("trainer tasks are still incomplete")

        try:
            output = self.aggregation.aggregate(round_record, tasks)
        except FedAvgLikeAggregationError as exc:
            raise AggregationError(str(exc)) from exc
        updated_round = self.rounds.upsert(
            replace(
                round_record,
                status=RoundStatus.AGGREGATING,
                aggregated_model_artifact_uri=output.artifact_uri,
                aggregated_model_artifact_hash=output.artifact_hash,
            )
        )
        return AggregationResult(
            round_record=updated_round,
            artifact_id=output.artifact_id,
            aggregated_model_artifact_uri=output.artifact_uri,
            aggregated_model_artifact_hash=output.artifact_hash,
            trainer_task_ids=output.trainer_task_ids,
            metadata={"sample_count": output.sample_count},
        )

    def seed_evaluation(self, round_record: Round) -> EvaluationSeedResult:
        if not round_record.aggregated_model_artifact_uri:
            raise EvaluationDispatchError("round has no aggregated model")
        if self.evaluation_tasks.list_by_round(round_record.round_id):
            raise EvaluationDispatchError("evaluation tasks already exist for round")

        feature_count = len(_EVALUATION_SAMPLES[0]["features"])
        manifest_artifact = self.artifacts.upload(
            kind=ArtifactKind.EVALUATION_INPUT_MANIFEST,
            name=f"job-{round_record.job_id}-round-{round_record.round_index}-evaluation-manifest.json",
            payload=json.dumps(
                {
                    "partition_id": f"job-{round_record.job_id}-round-{round_record.round_index}-evaluation",
                    "feature_count": feature_count,
                    "samples": _EVALUATION_SAMPLES,
                },
                sort_keys=True,
            ).encode("utf-8"),
            mime_type="application/json",
            metadata={"job_id": round_record.job_id, "round_id": round_record.round_id, "purpose": "evaluation"},
            job_id=round_record.job_id,
        )
        task = self.evaluation_tasks.upsert(
            EvaluationTask(
                evaluation_task_id=f"evaluation-task-{uuid4().hex}",
                job_id=round_record.job_id,
                round_id=round_record.round_id,
                source_training_task_id=None,
                evaluator_node_id=None,
                status=EvaluationTaskStatus.PENDING,
                target_model_artifact_uri=round_record.aggregated_model_artifact_uri,
                dataset_artifact_uri=manifest_artifact.uri,
                config_json={"accuracy_threshold": 0.75, "feature_count": feature_count},
            )
        )
        updated_round = self.rounds.upsert(replace(round_record, status=RoundStatus.EVALUATING))
        return EvaluationSeedResult(round_record=updated_round, evaluation_tasks=[task], artifact_ids=[manifest_artifact.artifact_id])

    def _partition_samples(self, partition_count: int) -> list[list[dict[str, object]]]:
        partitions = [[] for _ in range(partition_count)]
        for index, sample in enumerate(_DEMO_SAMPLES):
            partitions[index % partition_count].append(sample)
        return partitions

    def _require_job(self, job_id: int) -> Job:
        job = self.jobs.get(job_id)
        if job is None:
            raise ProtocolRunError("job not found")
        return job
