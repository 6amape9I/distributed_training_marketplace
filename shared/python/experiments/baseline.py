from __future__ import annotations

import json
import time
from pathlib import Path

from evaluator_agent.app.execution import EvaluationExecutor
from shared.python.experiments.wdbc import (
    DEFAULT_EPOCHS,
    DEFAULT_LEARNING_RATE,
    ensure_prepared_wdbc_dataset,
    experiments_output_dir,
)
from shared.python.schemas import EvaluationTaskRecord, TrainingTaskRecord
from shared.python.schemas.experiment import ExperimentBaselineSummary
from trainer_agent.app.execution import LocalFitExecutor



def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)



def run_baseline() -> ExperimentBaselineSummary:
    prepared = ensure_prepared_wdbc_dataset()
    output_dir = experiments_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    task = TrainingTaskRecord(
        task_id="baseline-local-fit",
        job_id=0,
        task_type="local_fit",
        status="running",
        model_artifact_uri="artifact://baseline-model-input",
        dataset_artifact_uri="artifact://baseline-train-manifest",
        config_json={
            "epochs": DEFAULT_EPOCHS,
            "learning_rate": DEFAULT_LEARNING_RATE,
            "feature_count": prepared.metadata.feature_count,
        },
    )
    model_payload = json.dumps(
        {"weights": [0.0] * prepared.metadata.feature_count, "bias": 0.0},
        sort_keys=True,
    ).encode("utf-8")
    train_payload = json.dumps(prepared.train_manifest, sort_keys=True).encode("utf-8")
    eval_payload = json.dumps(prepared.eval_manifest, sort_keys=True).encode("utf-8")

    fit_start = time.perf_counter()
    fit_artifacts = LocalFitExecutor().execute(
        task=task,
        trainer_node_id="baseline-trainer",
        model_payload=model_payload,
        dataset_payload=train_payload,
    )
    fit_runtime = time.perf_counter() - fit_start

    evaluation_task = EvaluationTaskRecord(
        evaluation_task_id="baseline-evaluation",
        job_id=0,
        round_id=None,
        source_training_task_id=task.task_id,
        evaluator_node_id="baseline-evaluator",
        status="running",
        target_model_artifact_uri="artifact://baseline-result-model",
        dataset_artifact_uri="artifact://baseline-eval-manifest",
        config_json={
            "accuracy_threshold": 0.75,
            "feature_count": prepared.metadata.feature_count,
        },
    )

    eval_start = time.perf_counter()
    eval_artifacts = EvaluationExecutor().execute(
        task=evaluation_task,
        model_payload=fit_artifacts.result_payload,
        dataset_payload=eval_payload,
    )
    eval_runtime = time.perf_counter() - eval_start

    model_path = output_dir / "baseline-model.json"
    train_report_path = output_dir / "baseline-trainer-report.json"
    evaluation_report_path = output_dir / "baseline-evaluation-report.json"
    summary_path = output_dir / "baseline-summary.json"

    model_path.write_bytes(fit_artifacts.result_payload)
    train_report_path.write_bytes(fit_artifacts.report_payload)
    evaluation_report_path.write_bytes(eval_artifacts.report_payload)

    train_report = json.loads(fit_artifacts.report_payload.decode("utf-8"))
    eval_report = json.loads(eval_artifacts.report_payload.decode("utf-8"))
    summary = ExperimentBaselineSummary(
        dataset_name=prepared.metadata.dataset_name,
        feature_count=prepared.metadata.feature_count,
        train_count=prepared.metadata.train_count,
        eval_count=prepared.metadata.eval_count,
        epochs=DEFAULT_EPOCHS,
        learning_rate=DEFAULT_LEARNING_RATE,
        fit_runtime_seconds=fit_runtime,
        evaluation_runtime_seconds=eval_runtime,
        total_runtime_seconds=fit_runtime + eval_runtime,
        train_accuracy=float(train_report["accuracy"]),
        train_average_loss=float(train_report["average_loss"]),
        eval_accuracy=float(eval_report["metrics"]["accuracy"]),
        eval_average_loss=float(eval_report["metrics"]["average_loss"]),
        accepted=bool(eval_report["acceptance_decision"]),
        result_model_path=_display_path(model_path),
        train_report_path=_display_path(train_report_path),
        evaluation_report_path=_display_path(evaluation_report_path),
    )
    summary_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return summary



def main() -> None:
    summary = run_baseline()
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
