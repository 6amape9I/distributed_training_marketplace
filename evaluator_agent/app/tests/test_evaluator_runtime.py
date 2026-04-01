from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluator_agent.app.application import EvaluatorRuntime
from evaluator_agent.app.execution import EvaluationExecutor
from evaluator_agent.app.settings import EvaluatorSettings
from evaluator_agent.app.storage import LocalWorkspace
from shared.python.hashing import digest_bytes
from shared.python.schemas import ArtifactRecord, EvaluationTaskRecord


class FakeOrchestratorClient:
    def __init__(self) -> None:
        self.registered = False
        self.heartbeats = 0
        self.uploaded: dict[str, bytes] = {}
        self.completed: list[tuple[str, str]] = []
        self.failed: list[tuple[str, str]] = []
        self.next_artifact_id = 1
        self.task = EvaluationTaskRecord(
            evaluation_task_id="evaluation-task-1",
            job_id=1,
            source_training_task_id="task-1",
            evaluator_node_id="evaluator-1",
            status="claimed",
            target_model_artifact_uri="artifact://model-result-1",
            dataset_artifact_uri="artifact://eval-manifest-1",
            config_json={"accuracy_threshold": 0.75, "feature_count": 3},
        )
        self.model_payload = json.dumps({"weights": [-2.0, -2.0, -2.0], "bias": 2.5}).encode("utf-8")
        self.dataset_payload = json.dumps(
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
        self.claimed = False

    def register_node(self, *, node_id: str, endpoint_url: str, capabilities: dict[str, Any] | None) -> dict[str, Any]:
        self.registered = True
        return {"node_id": node_id, "endpoint_url": endpoint_url, "capabilities": capabilities}

    def heartbeat(self, *, node_id: str) -> dict[str, Any]:
        self.heartbeats += 1
        return {"node_id": node_id, "status": "online"}

    def claim_task(self, *, evaluator_node_id: str) -> EvaluationTaskRecord | None:
        if self.claimed:
            return None
        self.claimed = True
        return self.task

    def start_task(self, *, evaluation_task_id: str, evaluator_node_id: str) -> EvaluationTaskRecord:
        return self.task

    def complete_task(
        self,
        *,
        evaluation_task_id: str,
        evaluator_node_id: str,
        report_artifact_id: str,
        metrics_json: dict[str, float | int | bool | str],
        sample_count: int,
        acceptance_decision: bool,
        target_model_digest: str,
    ) -> EvaluationTaskRecord:
        self.completed.append((evaluation_task_id, report_artifact_id))
        return self.task.model_copy(update={"status": "completed"})

    def fail_task(self, *, evaluation_task_id: str, evaluator_node_id: str, failure_reason: str) -> EvaluationTaskRecord:
        self.failed.append((evaluation_task_id, failure_reason))
        return self.task.model_copy(update={"status": "failed", "failure_reason": failure_reason})

    def upload_artifact(
        self,
        *,
        kind: str,
        name: str,
        payload: bytes,
        mime_type: str,
        metadata: dict[str, Any] | None = None,
        job_id: int | None = None,
        task_id: str | None = None,
    ) -> ArtifactRecord:
        artifact_id = f"artifact-{self.next_artifact_id}"
        self.next_artifact_id += 1
        self.uploaded[artifact_id] = payload
        return ArtifactRecord(
            artifact_id=artifact_id,
            kind=kind,
            uri=f"artifact://{artifact_id}",
            content_hash=digest_bytes(payload),
            content_size_bytes=len(payload),
            mime_type=mime_type,
            metadata_json=metadata,
            job_id=job_id,
            task_id=task_id,
        )

    def get_artifact_content(self, *, artifact_id: str) -> tuple[str, bytes]:
        if artifact_id == "model-result-1":
            return "application/json", self.model_payload
        return "application/json", self.dataset_payload


def test_evaluator_runtime_registers_heartbeats_and_completes_task(tmp_path: Path) -> None:
    settings = EvaluatorSettings(
        service_name="evaluator-agent",
        evaluator_node_id="evaluator-1",
        orchestrator_base_url="http://orchestrator.local",
        evaluator_bind_host="127.0.0.1",
        evaluator_bind_port=8020,
        evaluator_public_url="http://evaluator-1.local:8020",
        heartbeat_interval_seconds=1,
        task_poll_interval_seconds=1,
        local_workspace_path=str(tmp_path / "workspace"),
        evaluator_capabilities_json=None,
        enable_background_workers=False,
    )
    client = FakeOrchestratorClient()
    runtime = EvaluatorRuntime(
        settings=settings,
        orchestrator_client=client,
        executor=EvaluationExecutor(),
        workspace=LocalWorkspace(tmp_path / "workspace"),
    )

    runtime.ensure_registered()
    runtime.heartbeat_once()
    processed = runtime.poll_once()

    assert processed is True
    assert client.registered is True
    assert client.heartbeats == 1
    assert len(client.completed) == 1
    assert len(client.uploaded) == 1
    assert client.failed == []
    assert (tmp_path / "workspace" / "evaluation-task-1" / "evaluation-report.json").exists()
