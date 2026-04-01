from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trainer_agent.app.execution.local_fit_executor import LocalFitExecutor
from trainer_agent.app.orchestrator_client.protocol import OrchestratorClientProtocol
from trainer_agent.app.settings import TrainerSettings
from trainer_agent.app.storage.workspace import LocalWorkspace


@dataclass(slots=True)
class TrainerRuntimeState:
    registered: bool = False
    last_heartbeat_at: datetime | None = None
    current_task_id: str | None = None
    processed_tasks: int = 0
    last_error: str | None = None


class TrainerRuntime:
    def __init__(
        self,
        settings: TrainerSettings,
        orchestrator_client: OrchestratorClientProtocol,
        executor: LocalFitExecutor,
        workspace: LocalWorkspace,
    ) -> None:
        self.settings = settings
        self.orchestrator_client = orchestrator_client
        self.executor = executor
        self.workspace = workspace
        self.state = TrainerRuntimeState()
        self._state_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        if self._threads:
            return
        if not self.settings.enable_background_workers:
            return
        self._stop_event.clear()
        self._threads = [
            threading.Thread(target=self._heartbeat_loop, name=f"{self.settings.trainer_node_id}-heartbeat", daemon=True),
            threading.Thread(target=self._poll_loop, name=f"{self.settings.trainer_node_id}-poll", daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        for thread in self._threads:
            thread.join(timeout=2.0)
        self._threads.clear()
        close = getattr(self.orchestrator_client, "close", None)
        if callable(close):
            close()

    def status_payload(self) -> dict[str, object]:
        with self._state_lock:
            return {
                "service": self.settings.service_name,
                "trainer_node_id": self.settings.trainer_node_id,
                "registered": self.state.registered,
                "last_heartbeat_at": self.state.last_heartbeat_at.isoformat() if self.state.last_heartbeat_at else None,
                "current_task_id": self.state.current_task_id,
                "processed_tasks": self.state.processed_tasks,
                "last_error": self.state.last_error,
            }

    def ensure_registered(self) -> None:
        capabilities = None
        if self.settings.trainer_capabilities_json:
            capabilities = json.loads(self.settings.trainer_capabilities_json)
        self.orchestrator_client.register_node(
            node_id=self.settings.trainer_node_id,
            endpoint_url=self.settings.trainer_public_url,
            capabilities=capabilities,
        )
        with self._state_lock:
            self.state.registered = True
            self.state.last_error = None

    def heartbeat_once(self) -> None:
        try:
            if not self.state.registered:
                self.ensure_registered()
            self.orchestrator_client.heartbeat(node_id=self.settings.trainer_node_id)
            with self._state_lock:
                self.state.last_heartbeat_at = datetime.now(timezone.utc)
                self.state.last_error = None
        except Exception as exc:
            with self._state_lock:
                self.state.last_error = str(exc)
                self.state.registered = False

    def poll_once(self) -> bool:
        try:
            if not self.state.registered:
                self.ensure_registered()
            task = self.orchestrator_client.claim_task(trainer_node_id=self.settings.trainer_node_id)
            if task is None:
                return False
            with self._state_lock:
                self.state.current_task_id = task.task_id
                self.state.last_error = None
            self.orchestrator_client.start_task(task_id=task.task_id, trainer_node_id=self.settings.trainer_node_id)

            model_artifact_id = self._artifact_id_from_uri(task.model_artifact_uri)
            dataset_artifact_id = self._artifact_id_from_uri(task.dataset_artifact_uri)
            _, model_payload = self.orchestrator_client.get_artifact_content(artifact_id=model_artifact_id)
            _, dataset_payload = self.orchestrator_client.get_artifact_content(artifact_id=dataset_artifact_id)
            self.workspace.write_task_file(task.task_id, "model-input.json", model_payload)
            self.workspace.write_task_file(task.task_id, "dataset-manifest.json", dataset_payload)

            artifacts = self.executor.execute(
                task=task,
                trainer_node_id=self.settings.trainer_node_id,
                model_payload=model_payload,
                dataset_payload=dataset_payload,
            )
            self.workspace.write_task_file(task.task_id, "task-result.json", artifacts.result_payload)
            self.workspace.write_task_file(task.task_id, "trainer-report.json", artifacts.report_payload)

            result_artifact = self.orchestrator_client.upload_artifact(
                kind="task_result",
                name=f"{task.task_id}-result.json",
                payload=artifacts.result_payload,
                mime_type="application/json",
                metadata={
                    "trainer_node_id": self.settings.trainer_node_id,
                    "accuracy": artifacts.accuracy,
                    "round_id": task.round_id,
                },
                job_id=task.job_id,
                task_id=task.task_id,
            )
            report_artifact = self.orchestrator_client.upload_artifact(
                kind="trainer_report",
                name=f"{task.task_id}-report.json",
                payload=artifacts.report_payload,
                mime_type="application/json",
                metadata={
                    "trainer_node_id": self.settings.trainer_node_id,
                    "average_loss": artifacts.average_loss,
                    "round_id": task.round_id,
                },
                job_id=task.job_id,
                task_id=task.task_id,
            )
            self.orchestrator_client.complete_task(
                task_id=task.task_id,
                trainer_node_id=self.settings.trainer_node_id,
                result_artifact_id=result_artifact.artifact_id,
                report_artifact_id=report_artifact.artifact_id,
            )
            with self._state_lock:
                self.state.processed_tasks += 1
                self.state.current_task_id = None
                self.state.last_error = None
            return True
        except Exception as exc:
            current_task_id = None
            with self._state_lock:
                current_task_id = self.state.current_task_id
                self.state.last_error = str(exc)
            if current_task_id is not None:
                try:
                    self.orchestrator_client.fail_task(
                        task_id=current_task_id,
                        trainer_node_id=self.settings.trainer_node_id,
                        failure_reason=str(exc),
                    )
                except Exception:
                    pass
            with self._state_lock:
                self.state.current_task_id = None
            return False

    def _heartbeat_loop(self) -> None:
        while not self._stop_event.is_set():
            self.heartbeat_once()
            self._stop_event.wait(self.settings.heartbeat_interval_seconds)

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            processed = self.poll_once()
            if not processed:
                self._stop_event.wait(self.settings.task_poll_interval_seconds)

    def _artifact_id_from_uri(self, uri: str) -> str:
        if uri.startswith("artifact://"):
            return uri.split("artifact://", 1)[1]
        return Path(uri).name
