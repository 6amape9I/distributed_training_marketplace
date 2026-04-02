from __future__ import annotations

import json

from evaluator_agent.app.execution import EvaluationExecutor
from shared.python.schemas import EvaluationTaskRecord


def test_evaluation_executor_produces_metrics_and_acceptance() -> None:
    task = EvaluationTaskRecord(
        evaluation_task_id="evaluation-task-1",
        job_id=1,
        source_training_task_id="task-1",
        status="claimed",
        target_model_artifact_uri="artifact://result-1",
        dataset_artifact_uri="artifact://dataset-1",
        config_json={"accuracy_threshold": 0.75, "feature_count": 3},
        evaluator_node_id="evaluator-1",
    )
    model_payload = json.dumps({"weights": [-2.0, -2.0, -2.0], "bias": 2.5}).encode("utf-8")
    dataset_payload = json.dumps(
        {
            "partition_id": "eval-1",
            "samples": [
                {"features": [1.0, 1.1, 0.9], "label": 0},
                {"features": [0.9, 0.8, 1.0], "label": 0},
                {"features": [0.1, 0.2, 0.1], "label": 1},
                {"features": [0.2, 0.1, 0.2], "label": 1},
            ],
        }
    ).encode("utf-8")

    artifacts = EvaluationExecutor().execute(task=task, model_payload=model_payload, dataset_payload=dataset_payload)

    assert artifacts.sample_count == 4
    assert artifacts.metrics_json["accuracy"] >= 0.75
    assert artifacts.acceptance_decision is True
    assert artifacts.target_model_digest
    assert b'"acceptance_decision": true' in artifacts.report_payload


def test_evaluation_executor_prefers_manifest_feature_scales() -> None:
    executor = EvaluationExecutor()
    scales = executor._resolve_feature_scales(  # type: ignore[attr-defined]
        {"feature_scales": [5.0, 6.0, 7.0]},
        [{"features": [1.0, 2.0, 3.0], "label": 1}],
        3,
    )
    assert scales == [5.0, 6.0, 7.0]
