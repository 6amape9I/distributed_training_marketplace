from __future__ import annotations

import json
from pathlib import Path

from shared.python.experiments.report import build_report
from shared.python.schemas.experiment import ExperimentBaselineSummary, ExperimentDistributedSummary



def test_build_report_writes_json_markdown_and_plots(monkeypatch, tmp_path: Path) -> None:
    distributed = ExperimentDistributedSummary(
        dataset_name="wdbc",
        protocol_name="fedavg_like_wdbc_v1",
        job_id=1,
        round_id="round-1",
        final_job_status="ready_for_attestation",
        feature_count=30,
        train_count=455,
        eval_count=114,
        total_runtime_seconds=3.5,
        trainer_reports=[
            {"trainer_node_id": "trainer-1", "average_loss": 0.12},
            {"trainer_node_id": "trainer-2", "average_loss": 0.10},
        ],
        evaluation_metrics={"accuracy": 0.95, "average_loss": 0.14, "accepted": True, "threshold": 0.75},
        training_task_ids=["task-1", "task-2"],
        evaluation_task_id="evaluation-task-1",
        aggregated_model_artifact_uri="artifact://aggregated-model-1",
        aggregated_model_artifact_hash="hash-1",
    )
    baseline = ExperimentBaselineSummary(
        dataset_name="wdbc",
        feature_count=30,
        train_count=455,
        eval_count=114,
        epochs=12,
        learning_rate=0.5,
        fit_runtime_seconds=0.5,
        evaluation_runtime_seconds=0.1,
        total_runtime_seconds=0.6,
        train_accuracy=0.97,
        train_average_loss=0.08,
        eval_accuracy=0.96,
        eval_average_loss=0.11,
        accepted=True,
        result_model_path="artifacts/experiments/real-training/baseline-model.json",
        train_report_path="artifacts/experiments/real-training/baseline-trainer-report.json",
        evaluation_report_path="artifacts/experiments/real-training/baseline-evaluation-report.json",
    )

    (tmp_path / "distributed-summary.json").write_text(distributed.model_dump_json(indent=2), encoding="utf-8")
    (tmp_path / "baseline-summary.json").write_text(baseline.model_dump_json(indent=2), encoding="utf-8")
    monkeypatch.setattr("shared.python.experiments.report.experiments_output_dir", lambda: tmp_path)

    comparison = build_report()

    assert comparison.dataset_name == "wdbc"
    assert comparison.distributed_protocol_name == "fedavg_like_wdbc_v1"
    assert (tmp_path / "comparison.json").exists()
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "runtime_comparison.png").exists()
    assert (tmp_path / "accuracy_comparison.png").exists()
    assert (tmp_path / "trainer_loss_comparison.png").exists()

    comparison_json = json.loads((tmp_path / "comparison.json").read_text(encoding="utf-8"))
    assert comparison_json["distributed_eval_accuracy"] == 0.95
