from __future__ import annotations

import json
from pathlib import Path

from shared.python.experiments.wdbc import experiments_output_dir
from shared.python.schemas.experiment import (
    ExperimentBaselineSummary,
    ExperimentComparison,
    ExperimentDistributedSummary,
)



def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)



def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"required experiment artifact is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))



def _render_plots(
    *,
    output_dir: Path,
    baseline: ExperimentBaselineSummary,
    distributed: ExperimentDistributedSummary,
) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    runtime_path = output_dir / "runtime_comparison.png"
    accuracy_path = output_dir / "accuracy_comparison.png"
    loss_path = output_dir / "trainer_loss_comparison.png"

    plt.figure(figsize=(6, 4))
    plt.bar(
        ["distributed", "baseline"],
        [distributed.total_runtime_seconds, baseline.total_runtime_seconds],
        color=["#29524a", "#94a187"],
    )
    plt.ylabel("seconds")
    plt.title("Runtime Comparison")
    plt.tight_layout()
    plt.savefig(runtime_path)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.bar(
        ["distributed", "baseline"],
        [float(distributed.evaluation_metrics["accuracy"]), baseline.eval_accuracy],
        color=["#204e78", "#7aa6c2"],
    )
    plt.ylabel("accuracy")
    plt.ylim(0, 1)
    plt.title("Evaluation Accuracy")
    plt.tight_layout()
    plt.savefig(accuracy_path)
    plt.close()

    trainer_labels = [report["trainer_node_id"] for report in distributed.trainer_reports]
    trainer_losses = [float(report["average_loss"]) for report in distributed.trainer_reports]
    plt.figure(figsize=(7, 4))
    plt.bar(
        trainer_labels + ["baseline"],
        trainer_losses + [baseline.train_average_loss],
        color=["#8e6c88", "#b290a8", "#d8b384"],
    )
    plt.ylabel("average_loss")
    plt.title("Trainer Loss Comparison")
    plt.tight_layout()
    plt.savefig(loss_path)
    plt.close()

    return {
        "runtime_comparison": _display_path(runtime_path),
        "accuracy_comparison": _display_path(accuracy_path),
        "trainer_loss_comparison": _display_path(loss_path),
    }



def build_report() -> ExperimentComparison:
    output_dir = experiments_output_dir()
    distributed = ExperimentDistributedSummary.model_validate(_load_json(output_dir / "distributed-summary.json"))
    baseline = ExperimentBaselineSummary.model_validate(_load_json(output_dir / "baseline-summary.json"))
    plot_paths = _render_plots(output_dir=output_dir, baseline=baseline, distributed=distributed)

    comparison = ExperimentComparison(
        dataset_name=distributed.dataset_name,
        distributed_protocol_name=distributed.protocol_name,
        train_count=distributed.train_count,
        eval_count=distributed.eval_count,
        distributed_total_runtime_seconds=distributed.total_runtime_seconds,
        baseline_total_runtime_seconds=baseline.total_runtime_seconds,
        distributed_eval_accuracy=float(distributed.evaluation_metrics["accuracy"]),
        baseline_eval_accuracy=baseline.eval_accuracy,
        distributed_eval_average_loss=float(distributed.evaluation_metrics["average_loss"]),
        baseline_eval_average_loss=baseline.eval_average_loss,
        distributed_final_job_status=distributed.final_job_status,
        baseline_accepted=baseline.accepted,
        trainer_losses={
            report["trainer_node_id"]: float(report["average_loss"]) for report in distributed.trainer_reports
        },
        plot_paths=plot_paths,
    )
    (output_dir / "comparison.json").write_text(comparison.model_dump_json(indent=2), encoding="utf-8")

    report_md = output_dir / "report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Real Training Experiment",
                "",
                f"- Dataset: `{distributed.dataset_name}`",
                f"- Protocol: `{distributed.protocol_name}`",
                f"- Train / eval samples: `{distributed.train_count}` / `{distributed.eval_count}`",
                f"- Distributed final job status: `{distributed.final_job_status}`",
                f"- Distributed eval accuracy: `{float(distributed.evaluation_metrics['accuracy']):.4f}`",
                f"- Baseline eval accuracy: `{baseline.eval_accuracy:.4f}`",
                f"- Distributed eval loss: `{float(distributed.evaluation_metrics['average_loss']):.4f}`",
                f"- Baseline eval loss: `{baseline.eval_average_loss:.4f}`",
                f"- Distributed runtime: `{distributed.total_runtime_seconds:.4f}s`",
                f"- Baseline runtime: `{baseline.total_runtime_seconds:.4f}s`",
                "",
                "## Artifacts",
                "",
                f"- Comparison JSON: `{_display_path(output_dir / 'comparison.json')}`",
                f"- Runtime plot: `{plot_paths['runtime_comparison']}`",
                f"- Accuracy plot: `{plot_paths['accuracy_comparison']}`",
                f"- Trainer loss plot: `{plot_paths['trainer_loss_comparison']}`",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    return comparison



def main() -> None:
    comparison = build_report()
    print(comparison.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
