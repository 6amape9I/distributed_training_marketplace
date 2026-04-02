from __future__ import annotations

import json
from pathlib import Path

from shared.python.experiments.baseline import run_baseline
from shared.python.experiments.wdbc import build_prepared_wdbc_manifests


def test_build_prepared_wdbc_manifests_is_deterministic() -> None:
    first = build_prepared_wdbc_manifests()
    second = build_prepared_wdbc_manifests()

    assert first.metadata.source_record_count == 569
    assert first.metadata.feature_count == 30
    assert first.metadata.train_count == 455
    assert first.metadata.eval_count == 114
    assert [len(item["samples"]) for item in first.trainer_partition_manifests] == [228, 227]
    assert first.metadata.feature_names == second.metadata.feature_names
    assert first.metadata.feature_scales == second.metadata.feature_scales
    assert first.train_manifest["samples"][0] == second.train_manifest["samples"][0]
    assert first.eval_manifest["samples"][-1] == second.eval_manifest["samples"][-1]


def test_baseline_runner_writes_summary_and_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("shared.python.experiments.baseline.experiments_output_dir", lambda: tmp_path)

    summary = run_baseline()

    assert summary.train_count == 455
    assert summary.eval_count == 114
    assert 0 <= summary.train_accuracy <= 1
    assert 0 <= summary.eval_accuracy <= 1
    assert summary.accepted is True

    summary_json = json.loads((tmp_path / "baseline-summary.json").read_text(encoding="utf-8"))
    assert summary_json["dataset_name"] == "wdbc"
    assert (tmp_path / "baseline-model.json").exists()
    assert (tmp_path / "baseline-trainer-report.json").exists()
    assert (tmp_path / "baseline-evaluation-report.json").exists()
