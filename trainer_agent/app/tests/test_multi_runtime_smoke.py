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


class SharedFakeOrchestrator:
    def __init__(self) -> None:
        self.registered_nodes: set[str] = set()
        self.heartbeats: list[str] = []
        self.uploaded: dict[str, bytes] = {}
        self.completed: list[tuple[str, str, str, str]] = []
        self.failed: list[tuple[str, str, str]] = []
        self.next_artifact_id = 1
        self.model_payload = json.dumps({"weights": [0.0, 0.0, 0.0], "bias": 0.0}).encode("utf-8")
        self.dataset_payloads = {
            "dataset-1": json.dumps(
                {
                    "partition_id": "partition-1",
                    "samples": [
                        {"features": [1.0, 1.0, 0.9], "label": 1},
                        {"features": [0.8, 1.1, 0.7], "label": 1},
                        {"features": [0.1, 0.3, 0.2], "label": 0},
                        {"features": [0.2, 0.1, 0.4], "label": 0},
                    ],
                }
            ).encode("utf-8"),
            "dataset-2": json.dumps(
                {
                    "partition_id": "partition-2",
                    "samples": [
                        {"features": [1.2, 0.9, 1.0], "label": 1},
                        {"features": [0.9, 1.0, 0.8], "label": 1},
                        {"features": [0.2, 0.2, 0.3], "label": 0},
                        {"features": [0.3, 0.1, 0.2], "label": 0},
                    ],
                }
            ).encode("utf-8"),
        }
        self.tasks: dict[str, TrainingTaskRecord] = {
            "task-1": TrainingTaskRecord(
                task_id="task-1",
                job_id=77,
                task_type="local_fit",
                status="pending",
                data_partition_id="partition-1",
                model_artifact_uri="artifact://model-1",
                dataset_artifact_uri="artifact://dataset-1",
                config_json={"epochs": 6, "learning_rate": 0.5, "feature_count": 3},
            ),
            "task-2": TrainingTaskRecord(
                task_id="task-2",
                job_id=77,
                task_type="local_fit",
                status="pending",
                data_partition_id="partition-2",
                model_artifact_uri="artifact://model-1",
                dataset_artifact_uri="artifact://dataset-2",
                config_json={"epochs": 6, "learning_rate": 0.5, "feature_count": 3},
            ),
        }

    def register_node(self, *, node_id: str, endpoint_url: str, capabilities: dict[str, Any] | None) -> dict[str, Any]:
        self.registered_nodes.add(node_id)
        return {"node_id": node_id, "endpoint_url": endpoint_url, "capabilities": capabilities}

    def heartbeat(self, *, node_id: str) -> dict[str, Any]:
        self.heartbeats.append(node_id)
        return {"node_id": node_id, "status": "online"}

    def claim_task(self, *, trainer_node_id: str) -> TrainingTaskRecord | None:
        for task_id in sorted(self.tasks):
            task = self.tasks[task_id]
            if task.status == "pending":
                claimed = task.model_copy(update={"status": "claimed", "trainer_node_id": trainer_node_id})
                self.tasks[task_id] = claimed
                return claimed
        return None

    def start_task(self, *, task_id: str, trainer_node_id: str) -> TrainingTaskRecord:
        task = self.tasks[task_id]
        started = task.model_copy(update={"status": "running", "trainer_node_id": trainer_node_id})
        self.tasks[task_id] = started
        return started

    def complete_task(
        self,
        *,
        task_id: str,
        trainer_node_id: str,
        result_artifact_id: str,
        report_artifact_id: str,
    ) -> TrainingTaskRecord:
        task = self.tasks[task_id]
        completed = task.model_copy(
            update={
                "status": "completed",
                "trainer_node_id": trainer_node_id,
                "result_artifact_uri": f"artifact://{result_artifact_id}",
                "report_artifact_uri": f"artifact://{report_artifact_id}",
            }
        )
        self.tasks[task_id] = completed
        self.completed.append((task_id, trainer_node_id, result_artifact_id, report_artifact_id))
        return completed

    def fail_task(self, *, task_id: str, trainer_node_id: str, failure_reason: str) -> TrainingTaskRecord:
        task = self.tasks[task_id]
        failed = task.model_copy(update={"status": "failed", "failure_reason": failure_reason})
        self.tasks[task_id] = failed
        self.failed.append((task_id, trainer_node_id, failure_reason))
        return failed

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
        return "application/json", self.dataset_payloads[artifact_id]


def _build_runtime(node_id: str, port: int, tmp_path: Path, orchestrator: SharedFakeOrchestrator) -> TrainerRuntime:
    settings = TrainerSettings(
        service_name="trainer-agent",
        trainer_node_id=node_id,
        orchestrator_base_url="http://orchestrator.local",
        trainer_bind_host="127.0.0.1",
        trainer_bind_port=port,
        trainer_public_url=f"http://{node_id}.local:{port}",
        heartbeat_interval_seconds=1,
        task_poll_interval_seconds=1,
        local_workspace_path=str(tmp_path / node_id),
        artifact_upload_mode="orchestrator_http",
        trainer_capabilities_json=None,
        enable_background_workers=False,
    )
    return TrainerRuntime(
        settings=settings,
        orchestrator_client=orchestrator,
        executor=LocalFitExecutor(),
        workspace=LocalWorkspace(tmp_path / node_id),
    )


def test_two_trainer_runtimes_claim_distinct_tasks_and_complete(tmp_path: Path) -> None:
    orchestrator = SharedFakeOrchestrator()
    trainer_one = _build_runtime("trainer-1", 8010, tmp_path, orchestrator)
    trainer_two = _build_runtime("trainer-2", 8011, tmp_path, orchestrator)

    trainer_one.ensure_registered()
    trainer_two.ensure_registered()
    trainer_one.heartbeat_once()
    trainer_two.heartbeat_once()

    assert trainer_one.poll_once() is True
    assert trainer_two.poll_once() is True

    completed_task_ids = {entry[0] for entry in orchestrator.completed}
    claimed_trainers = {entry[1] for entry in orchestrator.completed}

    assert orchestrator.registered_nodes == {"trainer-1", "trainer-2"}
    assert claimed_trainers == {"trainer-1", "trainer-2"}
    assert completed_task_ids == {"task-1", "task-2"}
    assert len(orchestrator.uploaded) == 4
    assert orchestrator.failed == []
    assert (tmp_path / "trainer-1" / "task-1" / "task-result.json").exists()
    assert (tmp_path / "trainer-2" / "task-2" / "task-result.json").exists()
