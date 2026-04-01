from __future__ import annotations

import json

from shared.python.schemas import TrainingTaskRecord
from trainer_agent.app.execution import LocalFitExecutor


def test_local_fit_executor_produces_real_result_and_report() -> None:
    executor = LocalFitExecutor()
    task = TrainingTaskRecord(
        task_id="task-1",
        job_id=1,
        task_type="local_fit",
        status="running",
        model_artifact_uri="artifact://model-1",
        dataset_artifact_uri="artifact://dataset-1",
        config_json={"epochs": 8, "learning_rate": 0.5, "feature_count": 3},
    )
    model_payload = json.dumps({"weights": [0.0, 0.0, 0.0], "bias": 0.0}).encode("utf-8")
    dataset_payload = json.dumps(
        {
            "partition_id": "partition-1",
            "samples": [
                {"features": [1.0, 1.0, 0.8], "label": 1},
                {"features": [0.9, 1.1, 0.7], "label": 1},
                {"features": [0.1, 0.2, 0.3], "label": 0},
                {"features": [0.2, 0.1, 0.4], "label": 0},
            ],
        }
    ).encode("utf-8")

    result = executor.execute(
        task=task,
        trainer_node_id="trainer-1",
        model_payload=model_payload,
        dataset_payload=dataset_payload,
    )

    model_out = json.loads(result.result_payload.decode("utf-8"))
    report_out = json.loads(result.report_payload.decode("utf-8"))
    assert any(abs(weight) > 0 for weight in model_out["weights"])
    assert 0 <= report_out["accuracy"] <= 1
    assert report_out["sample_count"] == 4
