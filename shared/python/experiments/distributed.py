from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx

from shared.python.experiments.wdbc import ensure_prepared_wdbc_dataset, experiments_output_dir
from shared.python.schemas.experiment import ExperimentDistributedSummary

EXPERIMENT_PROTOCOL_NAME = "fedavg_like_wdbc_v1"


class DistributedExperimentError(ValueError):
    pass



def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]



def _load_demo_state() -> dict[str, str]:
    state_path = _repo_root() / "tmp" / "demo-state" / "current-run.env"
    if not state_path.exists():
        raise DistributedExperimentError(f"demo state file not found: {state_path}. Run make demo-init first.")
    state: dict[str, str] = {}
    for line in state_path.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        state[key] = value
    return state



def _artifact_id(uri: str) -> str:
    if not uri.startswith("artifact://"):
        raise DistributedExperimentError(f"unsupported artifact uri: {uri}")
    return uri.split("artifact://", 1)[1]



def _get_json(client: httpx.Client, path: str) -> object:
    response = client.get(path)
    response.raise_for_status()
    return response.json()



def _post_json(client: httpx.Client, path: str) -> object:
    response = client.post(path)
    response.raise_for_status()
    return response.json()



def _artifact_content(client: httpx.Client, uri: str) -> object:
    artifact_id = _artifact_id(uri)
    payload = _get_json(client, f"/artifacts/{artifact_id}/content")
    assert isinstance(payload, dict)
    return json.loads(base64.b64decode(payload["payload_base64"]).decode("utf-8"))



def run_distributed(orchestrator_base_url: str = "http://127.0.0.1:8000") -> ExperimentDistributedSummary:
    prepared = ensure_prepared_wdbc_dataset()
    state = _load_demo_state()
    job_id = int(state.get("JOB_ID", "0") or 0)
    if job_id <= 0:
        raise DistributedExperimentError("JOB_ID is missing from demo state")

    output_dir = experiments_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    with httpx.Client(base_url=orchestrator_base_url, timeout=10.0, trust_env=False) as client:
        client.get("/health").raise_for_status()
        job = _get_json(client, f"/jobs/{job_id}")
        assert isinstance(job, dict)
        if job["offchain_status"] != "scheduling":
            raise DistributedExperimentError(
                f"job {job_id} must be in scheduling before experiment start, got {job['offchain_status']}"
            )
        rounds = _get_json(client, f"/jobs/{job_id}/rounds")
        assert isinstance(rounds, list)
        if rounds:
            raise DistributedExperimentError(
                f"job {job_id} already has rounds; run make demo-clean && make demo-up && make demo-init"
            )

        start_ts = time.perf_counter()
        query = urlencode({"protocol_name": EXPERIMENT_PROTOCOL_NAME})
        start_response = _post_json(client, f"/internal/protocol-runs/start-for-job/{job_id}?{query}")
        assert isinstance(start_response, dict)
        round_id = str(start_response["round_id"])

        while True:
            training_tasks = _get_json(client, f"/jobs/{job_id}/training-tasks")
            assert isinstance(training_tasks, list)
            statuses = [task["status"] for task in training_tasks]
            if statuses and all(status == "completed" for status in statuses):
                break
            if any(status == "failed" for status in statuses):
                raise DistributedExperimentError("at least one trainer task failed")
            time.sleep(2)

        _post_json(client, f"/internal/rounds/{round_id}/reconcile")

        while True:
            evaluation_tasks = _get_json(client, f"/jobs/{job_id}/evaluation-tasks")
            assert isinstance(evaluation_tasks, list)
            statuses = [task["status"] for task in evaluation_tasks]
            if statuses and all(status == "completed" for status in statuses):
                break
            if any(status == "failed" for status in statuses):
                raise DistributedExperimentError("evaluation task failed")
            time.sleep(2)

        _post_json(client, f"/internal/rounds/{round_id}/reconcile")
        total_runtime = time.perf_counter() - start_ts

        job = _get_json(client, f"/jobs/{job_id}")
        round_record = _get_json(client, f"/rounds/{round_id}")
        training_tasks = _get_json(client, f"/jobs/{job_id}/training-tasks")
        evaluation_tasks = _get_json(client, f"/jobs/{job_id}/evaluation-tasks")
        assert isinstance(job, dict)
        assert isinstance(round_record, dict)
        assert isinstance(training_tasks, list)
        assert isinstance(evaluation_tasks, list)
        if len(evaluation_tasks) != 1:
            raise DistributedExperimentError(f"expected one evaluation task, got {len(evaluation_tasks)}")

        trainer_reports = []
        for task in training_tasks:
            if not task.get("report_artifact_uri"):
                raise DistributedExperimentError(f"task {task['task_id']} is missing trainer report artifact")
            report = _artifact_content(client, str(task["report_artifact_uri"]))
            assert isinstance(report, dict)
            trainer_reports.append(report)

        evaluation_task = evaluation_tasks[0]
        if not evaluation_task.get("report_artifact_uri"):
            raise DistributedExperimentError("evaluation task is missing report artifact")
        evaluation_report = _artifact_content(client, str(evaluation_task["report_artifact_uri"]))
        assert isinstance(evaluation_report, dict)

    summary = ExperimentDistributedSummary(
        dataset_name=prepared.metadata.dataset_name,
        protocol_name=EXPERIMENT_PROTOCOL_NAME,
        job_id=job_id,
        round_id=round_id,
        final_job_status=str(job["offchain_status"]),
        feature_count=prepared.metadata.feature_count,
        train_count=prepared.metadata.train_count,
        eval_count=prepared.metadata.eval_count,
        total_runtime_seconds=total_runtime,
        trainer_reports=trainer_reports,
        evaluation_metrics=dict(evaluation_report["metrics"]),
        training_task_ids=[str(task["task_id"]) for task in training_tasks],
        evaluation_task_id=str(evaluation_task["evaluation_task_id"]),
        aggregated_model_artifact_uri=str(round_record["aggregated_model_artifact_uri"]),
        aggregated_model_artifact_hash=round_record.get("aggregated_model_artifact_hash"),
    )
    (output_dir / "distributed-summary.json").write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    (_repo_root() / "tmp" / "experiment-state").mkdir(parents=True, exist_ok=True)
    (_repo_root() / "tmp" / "experiment-state" / "current-run.json").write_text(
        json.dumps(
            {
                "job_id": job_id,
                "round_id": round_id,
                "protocol_name": EXPERIMENT_PROTOCOL_NAME,
                "final_job_status": summary.final_job_status,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return summary



def main() -> None:
    summary = run_distributed()
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
