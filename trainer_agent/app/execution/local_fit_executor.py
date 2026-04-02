from __future__ import annotations

import json
import math
from dataclasses import dataclass

from shared.python.hashing import digest_bytes
from shared.python.schemas import TrainerReport, TrainingTaskRecord


@dataclass(slots=True, frozen=True)
class ExecutionArtifacts:
    result_payload: bytes
    report_payload: bytes
    accuracy: float
    average_loss: float


class LocalFitExecutor:
    def execute(
        self,
        *,
        task: TrainingTaskRecord,
        trainer_node_id: str,
        model_payload: bytes,
        dataset_payload: bytes,
    ) -> ExecutionArtifacts:
        model = json.loads(model_payload.decode("utf-8"))
        manifest = json.loads(dataset_payload.decode("utf-8"))
        samples = manifest["samples"]
        feature_count = int(task.config_json.get("feature_count", len(samples[0]["features"])))
        epochs = int(task.config_json.get("epochs", 8))
        learning_rate = float(task.config_json.get("learning_rate", 0.5))

        weights = [float(value) for value in model.get("weights", [0.0] * feature_count)]
        bias = float(model.get("bias", 0.0))
        scales = self._resolve_feature_scales(manifest, samples, feature_count)
        losses: list[float] = []

        for _ in range(epochs):
            epoch_loss = 0.0
            for sample in samples:
                features = self._normalize(sample["features"], scales)
                label = float(sample["label"])
                prediction = self._sigmoid(sum(weight * value for weight, value in zip(weights, features)) + bias)
                error = prediction - label
                for index in range(feature_count):
                    weights[index] -= learning_rate * error * features[index]
                bias -= learning_rate * error
                epoch_loss += self._binary_cross_entropy(prediction, label)
            losses.append(epoch_loss / len(samples))

        correct = 0
        for sample in samples:
            features = self._normalize(sample["features"], scales)
            prediction = self._sigmoid(sum(weight * value for weight, value in zip(weights, features)) + bias)
            predicted_label = 1 if prediction >= 0.5 else 0
            if predicted_label == int(sample["label"]):
                correct += 1
        accuracy = correct / len(samples)
        average_loss = sum(losses) / len(losses)

        result_payload = json.dumps(
            {
                "weights": weights,
                "bias": bias,
                "epochs": epochs,
                "learning_rate": learning_rate,
                "partition_id": manifest["partition_id"],
                "sample_count": len(samples),
            },
            sort_keys=True,
        ).encode("utf-8")
        report = TrainerReport(
            task_id=task.task_id,
            trainer_node_id=trainer_node_id,
            data_partition_id=manifest["partition_id"],
            sample_count=len(samples),
            epochs=epochs,
            learning_rate=learning_rate,
            average_loss=average_loss,
            accuracy=accuracy,
            model_digest=digest_bytes(result_payload),
        )
        return ExecutionArtifacts(
            result_payload=result_payload,
            report_payload=report.model_dump_json(indent=2).encode("utf-8"),
            accuracy=accuracy,
            average_loss=average_loss,
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
