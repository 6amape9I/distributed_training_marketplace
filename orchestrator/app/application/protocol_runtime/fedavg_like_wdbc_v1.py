from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from orchestrator.app.application.protocol_runtime.fedavg_like_v1 import FedAvgLikeV1Protocol, ProtocolRunError
from orchestrator.app.application.protocol_runtime.types import EvaluationSeedResult, RoundPlan
from orchestrator.app.application.services.evaluation_dispatch_service import EvaluationDispatchError
from orchestrator.app.domain.entities import EvaluationTask, Job, Node, Round, TrainingTask
from orchestrator.app.domain.enums import ArtifactKind, EvaluationTaskStatus, RoundStatus, TrainingTaskStatus, TrainingTaskType
from shared.python.experiments import DEFAULT_EPOCHS, DEFAULT_LEARNING_RATE, prepared_wdbc_dir
from shared.python.schemas import PreparedDatasetMetadata


class PreparedDatasetError(ValueError):
    pass


class FedAvgLikeWdbcV1Protocol(FedAvgLikeV1Protocol):
    protocol_name = "fedavg_like_wdbc_v1"

    def prepare_round(self, job: Job, round_record: Round, trainer_count: int) -> RoundPlan:
        metadata = self._metadata()
        if trainer_count != metadata.trainer_partition_count:
            raise ProtocolRunError(
                f"{self.protocol_name} requires exactly {metadata.trainer_partition_count} online trainers, got {trainer_count}"
            )

        model_artifact = self.artifacts.upload(
            kind=ArtifactKind.MODEL_INPUT,
            name=f"job-{job.job_id}-round-{round_record.round_index}-base-model.json",
            payload=json.dumps({"weights": [0.0] * metadata.feature_count, "bias": 0.0}, sort_keys=True).encode("utf-8"),
            mime_type="application/json",
            metadata={
                "job_id": job.job_id,
                "round_id": round_record.round_id,
                "feature_count": metadata.feature_count,
                "dataset_name": metadata.dataset_name,
            },
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

        metadata = self._metadata()
        if len(trainers) != metadata.trainer_partition_count:
            raise ProtocolRunError(
                f"{self.protocol_name} requires exactly {metadata.trainer_partition_count} online trainers, got {len(trainers)}"
            )

        created_tasks: list[TrainingTask] = []
        for index, trainer in enumerate(sorted(trainers, key=lambda item: item.node_id), start=1):
            manifest = self._load_json(f"partition-trainer-{index}.json")
            partition_id = str(manifest["partition_id"])
            dataset_artifact = self.artifacts.upload(
                kind=ArtifactKind.DATASET_MANIFEST,
                name=f"{partition_id}.json",
                payload=json.dumps(manifest, sort_keys=True).encode("utf-8"),
                mime_type="application/json",
                metadata={
                    "job_id": round_record.job_id,
                    "round_id": round_record.round_id,
                    "trainer_hint": trainer.node_id,
                    "dataset_name": metadata.dataset_name,
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
                config_json={
                    "epochs": DEFAULT_EPOCHS,
                    "learning_rate": DEFAULT_LEARNING_RATE,
                    "feature_count": metadata.feature_count,
                },
            )
            created_tasks.append(self.training_tasks.upsert(task))
        self.rounds.upsert(replace(round_record, status=RoundStatus.TRAINING))
        return created_tasks

    def seed_evaluation(self, round_record: Round) -> EvaluationSeedResult:
        if not round_record.aggregated_model_artifact_uri:
            raise EvaluationDispatchError("round has no aggregated model")
        if self.evaluation_tasks.list_by_round(round_record.round_id):
            raise EvaluationDispatchError("evaluation tasks already exist for round")

        metadata = self._metadata()
        manifest = self._load_json("eval.json")
        manifest_artifact = self.artifacts.upload(
            kind=ArtifactKind.EVALUATION_INPUT_MANIFEST,
            name=f"job-{round_record.job_id}-round-{round_record.round_index}-evaluation-manifest.json",
            payload=json.dumps(manifest, sort_keys=True).encode("utf-8"),
            mime_type="application/json",
            metadata={
                "job_id": round_record.job_id,
                "round_id": round_record.round_id,
                "purpose": "evaluation",
                "dataset_name": metadata.dataset_name,
            },
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
                config_json={"accuracy_threshold": 0.75, "feature_count": metadata.feature_count},
            )
        )
        updated_round = self.rounds.upsert(replace(round_record, status=RoundStatus.EVALUATING))
        return EvaluationSeedResult(round_record=updated_round, evaluation_tasks=[task], artifact_ids=[manifest_artifact.artifact_id])

    def _metadata(self) -> PreparedDatasetMetadata:
        return PreparedDatasetMetadata.model_validate(self._load_json("processed.json"))

    def _load_json(self, file_name: str) -> dict[str, object]:
        path = self._data_dir() / file_name
        if not path.exists():
            raise PreparedDatasetError(f"prepared dataset file is missing: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _data_dir(self) -> Path:
        return prepared_wdbc_dir()
