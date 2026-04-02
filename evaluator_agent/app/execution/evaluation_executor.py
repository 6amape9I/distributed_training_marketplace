from __future__ import annotations

import json
import math
from dataclasses import dataclass

from shared.python.hashing import digest_bytes
from shared.python.schemas import EvaluationTaskRecord


@dataclass(slots=True, frozen=True)
class EvaluationArtifacts:
    report_payload: bytes
    metrics_json: dict[str, float | int | bool | str]
    sample_count: int
    acceptance_decision: bool
    target_model_digest: str


class EvaluationExecutor:
    def execute(
        self,
        *,
        task: EvaluationTaskRecord,
        model_payload: bytes,
        dataset_payload: bytes,
    ) -> EvaluationArtifacts:
        model = json.loads(model_payload.decode("utf-8"))
        manifest = json.loads(dataset_payload.decode("utf-8"))
        samples = manifest["samples"]
        feature_count = int(task.config_json.get("feature_count", len(samples[0]["features"])))
        threshold = float(task.config_json.get("accuracy_threshold", 0.75))

        weights = [float(value) for value in model.get("weights", [0.0] * feature_count)]
        bias = float(model.get("bias", 0.0))
        scales = self._resolve_feature_scales(manifest, samples, feature_count)
        losses: list[float] = []
        correct = 0

        for sample in samples:
            features = self._normalize(sample["features"], scales)
            label = float(sample["label"])
            prediction = self._sigmoid(sum(weight * value for weight, value in zip(weights, features)) + bias)
            losses.append(self._binary_cross_entropy(prediction, label))
            predicted_label = 1 if prediction >= 0.5 else 0
            if predicted_label == int(label):
                correct += 1

        sample_count = len(samples)
        accuracy = correct / sample_count
        average_loss = sum(losses) / sample_count
        acceptance_decision = accuracy >= threshold
        target_model_digest = digest_bytes(model_payload)
        metrics_json = {
            "accuracy": accuracy,
            "average_loss": average_loss,
            "threshold": threshold,
            "accepted": acceptance_decision,
        }
        report_payload = json.dumps(
            {
                "evaluation_task_id": task.evaluation_task_id,
                "job_id": task.job_id,
                "source_training_task_id": task.source_training_task_id,
                "sample_count": sample_count,
                "metrics": metrics_json,
                "acceptance_decision": acceptance_decision,
                "target_model_digest": target_model_digest,
            },
            sort_keys=True,
            indent=2,
        ).encode("utf-8")
        return EvaluationArtifacts(
            report_payload=report_payload,
            metrics_json=metrics_json,
            sample_count=sample_count,
            acceptance_decision=acceptance_decision,
            target_model_digest=target_model_digest,
        )

    def _resolve_feature_scales(
        self,
        manifest: dict[str, object],
        samples: list[dict[str, object]],
        feature_count: int,
    ) -> list[float]:
        raw_scales = manifest.get("feature_scales")
        if isinstance(raw_scales, list) and len(raw_scales) == feature_count:
            return [max(abs(float(value)), 1.0) for value in raw_scales]
        return self._feature_scales(samples, feature_count)

    def _feature_scales(self, samples: list[dict[str, object]], feature_count: int) -> list[float]:
        scales = [1.0] * feature_count
        for index in range(feature_count):
            max_value = max(abs(float(sample["features"][index])) for sample in samples)
            scales[index] = max(max_value, 1.0)
        return scales

    def _normalize(self, features: list[float], scales: list[float]) -> list[float]:
        return [float(value) / scale for value, scale in zip(features, scales)]

    def _sigmoid(self, value: float) -> float:
        bounded = max(min(value, 30.0), -30.0)
        return 1.0 / (1.0 + math.exp(-bounded))

    def _binary_cross_entropy(self, prediction: float, label: float) -> float:
        prediction = min(max(prediction, 1e-9), 1 - 1e-9)
        return -(label * math.log(prediction) + (1 - label) * math.log(1 - prediction))
