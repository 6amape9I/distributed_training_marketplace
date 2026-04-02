from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PreparedDatasetMetadata(BaseModel):
    dataset_name: str
    source_path: str
    source_record_count: int = Field(ge=1)
    feature_names: list[str]
    feature_count: int = Field(ge=1)
    label_mapping: dict[str, int]
    feature_scales: list[float]
    split_seed: int
    train_ratio: float = Field(gt=0, lt=1)
    train_count: int = Field(ge=1)
    eval_count: int = Field(ge=1)
    trainer_partition_count: int = Field(ge=1)


class ExperimentDistributedSummary(BaseModel):
    dataset_name: str
    protocol_name: str
    job_id: int
    round_id: str
    final_job_status: str
    feature_count: int = Field(ge=1)
    train_count: int = Field(ge=1)
    eval_count: int = Field(ge=1)
    total_runtime_seconds: float = Field(ge=0)
    trainer_reports: list[dict[str, Any]]
    evaluation_metrics: dict[str, Any]
    training_task_ids: list[str]
    evaluation_task_id: str
    aggregated_model_artifact_uri: str
    aggregated_model_artifact_hash: str | None = None


class ExperimentBaselineSummary(BaseModel):
    dataset_name: str
    feature_count: int = Field(ge=1)
    train_count: int = Field(ge=1)
    eval_count: int = Field(ge=1)
    epochs: int = Field(ge=1)
    learning_rate: float = Field(gt=0)
    fit_runtime_seconds: float = Field(ge=0)
    evaluation_runtime_seconds: float = Field(ge=0)
    total_runtime_seconds: float = Field(ge=0)
    train_accuracy: float = Field(ge=0, le=1)
    train_average_loss: float = Field(ge=0)
    eval_accuracy: float = Field(ge=0, le=1)
    eval_average_loss: float = Field(ge=0)
    accepted: bool
    result_model_path: str
    train_report_path: str
    evaluation_report_path: str


class ExperimentComparison(BaseModel):
    dataset_name: str
    distributed_protocol_name: str
    train_count: int = Field(ge=1)
    eval_count: int = Field(ge=1)
    distributed_total_runtime_seconds: float = Field(ge=0)
    baseline_total_runtime_seconds: float = Field(ge=0)
    distributed_eval_accuracy: float = Field(ge=0, le=1)
    baseline_eval_accuracy: float = Field(ge=0, le=1)
    distributed_eval_average_loss: float = Field(ge=0)
    baseline_eval_average_loss: float = Field(ge=0)
    distributed_final_job_status: str
    baseline_accepted: bool
    trainer_losses: dict[str, float]
    plot_paths: dict[str, str]
