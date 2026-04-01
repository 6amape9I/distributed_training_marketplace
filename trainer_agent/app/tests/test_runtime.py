from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.python.hashing import digest_bytes
from shared.python.schemas import ArtifactRecord, TrainingTaskRecord
from trainer_agent.app.application import TrainerRuntime
from trainer_agent.app.execution import LocalFitExecutor
from trainer_agent.app.settings import TrainerSettings
from trainer_agent.app.storage import LocalWorkspace


class FakeOrchestratorClient:
    def __init__(self) -> None:
        self.registered = False
        self.heartbeats = 0
        self.uploaded: dict[str, bytes] = {}
        self.completed: list[tuple[str, str, str]] = []
        self.failed: list[tuple[str, str]] = []
        self.next_artifact_id = 1
        self.task = TrainingTaskRecord(
            task_id="task-1",
            job_id=1,
            task_type="local_fit",
            status="claimed",
            model_artifact_uri="artifact://model-1",
            dataset_artifact_uri="artifact://dataset-1",
            config_json={"epochs": 6, "learning_rate": 0.5, "feature_count": 3},
            data_partition_id="partition-1",
            trainer_node_id="trainer-1",
        )
        self.model_payload = json.dumps({"weights": [0.0, 0.0, 0.0], "bias": 0.0}).encode("utf-8")
        self.dataset_payload = json.dumps(
            {
                "partition_id": "partition-1",
                "samples": [
                    {"features": [1.0, 1.0, 0.9], "label": 1},
                    {"features": [0.8, 1.1, 0.7], "label": 1},
                    {"features": [0.1, 0.3, 0.2], "label": 0},
                    {"features": [0.2, 0.1, 0.4], "label": 0},
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

    def claim_task(self, *, trainer_node_id: str) -> TrainingTaskRecord | None:
        if self.claimed:
            return None
        self.claimed = True
        return self.task

    def start_task(self, *, task_id: str, trainer_node_id: str) -> TrainingTaskRecord:
        return self.task

    def complete_task(
        self,
        *,
        task_id: str,
        trainer_node_id: str,
        result_artifact_id: str,
        report_artifact_id: str,
    ) -> TrainingTaskRecord:
        self.completed.append((task_id, result_artifact_id, report_artifact_id))
        return self.task.model_copy(update={"status": "completed"})

    def fail_task(self, *, task_id: str, trainer_node_id: str, failure_reason: str) -> TrainingTaskRecord:
        self.failed.append((task_id, failure_reason))
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
        if artifact_id == "model-1":
            return "application/json", self.model_payload
        return "application/json", self.dataset_payload


def test_trainer_runtime_registers_heartbeats_and_completes_task(tmp_path: Path) -> None:
    settings = TrainerSettings(
        service_name="trainer-agent",
        trainer_node_id="trainer-1",
        orchestrator_base_url="http://orchestrator.local",
        trainer_bind_host="127.0.0.1",
        trainer_bind_port=8010,
        trainer_public_url="http://trainer-1.local:8010",
        heartbeat_interval_seconds=1,
        task_poll_interval_seconds=1,
        local_workspace_path=str(tmp_path / "workspace"),
        artifact_upload_mode="orchestrator_http",
        trainer_capabilities_json=None,
        enable_background_workers=False,
    )
    client = FakeOrchestratorClient()
    runtime = TrainerRuntime(
        settings=settings,
        orchestrator_client=client,
        executor=LocalFitExecutor(),
        workspace=LocalWorkspace(tmp_path / "workspace"),
    )

    runtime.ensure_registered()
    runtime.heartbeat_once()
    processed = runtime.poll_once()

    assert processed is True
    assert client.registered is True
    assert client.heartbeats == 1
    assert len(client.completed) == 1
    assert len(client.uploaded) == 2
    assert client.failed == []
    assert (tmp_path / "workspace" / "task-1" / "task-result.json").exists()
    assert (tmp_path / "workspace" / "task-1" / "trainer-report.json").exists()
