from __future__ import annotations

import json

from orchestrator.app.application.protocol_runtime.types import AggregationArtifacts
from orchestrator.app.application.services.artifact_service import ArtifactService
from orchestrator.app.domain.entities import Round, TrainingTask
from orchestrator.app.domain.enums import ArtifactKind


class FedAvgLikeAggregationError(ValueError):
    pass

class FedAvgLikeAggregationService:
    def __init__(self, artifacts: ArtifactService) -> None:
        self.artifacts = artifacts

    def aggregate(self, round_record: Round, tasks: list[TrainingTask]) -> AggregationArtifacts:
        weights_accumulator: list[float] | None = None
        bias_accumulator = 0.0
        total_samples = 0
        trainer_task_ids: list[str] = []

        for task in tasks:
            if not task.result_artifact_uri:
                raise FedAvgLikeAggregationError("trainer task missing result artifact")
            artifact_id = self._artifact_id_from_uri(task.result_artifact_uri)
            payload = self.artifacts.read_content(artifact_id)
            try:
                result = json.loads(payload.decode("utf-8"))
                weights = [float(value) for value in result["weights"]]
                bias = float(result["bias"])
                sample_count = int(result["sample_count"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise FedAvgLikeAggregationError(f"malformed trainer result for task {task.task_id}") from exc
            if sample_count <= 0:
                raise FedAvgLikeAggregationError("trainer result has non-positive sample_count")
            if weights_accumulator is None:
                weights_accumulator = [0.0] * len(weights)
            if len(weights) != len(weights_accumulator):
                raise FedAvgLikeAggregationError("trainer result dimensions are incompatible")
            for index, value in enumerate(weights):
                weights_accumulator[index] += value * sample_count
            bias_accumulator += bias * sample_count
            total_samples += sample_count
            trainer_task_ids.append(task.task_id)

        if weights_accumulator is None or total_samples <= 0:
            raise FedAvgLikeAggregationError("round produced no aggregation inputs")

        aggregated_weights = [value / total_samples for value in weights_accumulator]
        aggregated_bias = bias_accumulator / total_samples
        aggregated_payload = json.dumps(
            {
                "weights": aggregated_weights,
                "bias": aggregated_bias,
                "round_id": round_record.round_id,
                "trainer_task_ids": trainer_task_ids,
                "sample_count": total_samples,
            },
            sort_keys=True,
        ).encode("utf-8")
        artifact = self.artifacts.upload(
            kind=ArtifactKind.MODEL_INPUT,
            name=f"job-{round_record.job_id}-round-{round_record.round_index}-aggregated-model.json",
            payload=aggregated_payload,
            mime_type="application/json",
            metadata={
                "job_id": round_record.job_id,
                "round_id": round_record.round_id,
                "protocol_name": round_record.protocol_name,
                "trainer_task_ids": trainer_task_ids,
                "sample_count": total_samples,
            },
            job_id=round_record.job_id,
        )
        return AggregationArtifacts(
            artifact_id=artifact.artifact_id,
            artifact_uri=artifact.uri,
            artifact_hash=artifact.content_hash,
            trainer_task_ids=trainer_task_ids,
            sample_count=total_samples,
        )

    def _artifact_id_from_uri(self, uri: str) -> str:
        if uri.startswith("artifact://"):
            return uri.split("artifact://", 1)[1]
        return uri
