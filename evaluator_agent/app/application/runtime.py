from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from evaluator_agent.app.execution.evaluation_executor import EvaluationExecutor
from evaluator_agent.app.orchestrator_client.protocol import OrchestratorClientProtocol
from evaluator_agent.app.settings import EvaluatorSettings
from evaluator_agent.app.storage.workspace import LocalWorkspace


@dataclass(slots=True)
class EvaluatorRuntimeState:
    registered: bool = False
    last_heartbeat_at: datetime | None = None
    current_task_id: str | None = None
    processed_tasks: int = 0
    last_error: str | None = None


class EvaluatorRuntime:
    def __init__(
        self,
        settings: EvaluatorSettings,
        orchestrator_client: OrchestratorClientProtocol,
        executor: EvaluationExecutor,
        workspace: LocalWorkspace,
    ) -> None:
        self.settings = settings
        self.orchestrator_client = orchestrator_client
        self.executor = executor
        self.workspace = workspace
        self.state = EvaluatorRuntimeState()
        self._state_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        if self._threads or not self.settings.enable_background_workers:
            return
        self._stop_event.clear()
        self._threads = [
            threading.Thread(target=self._heartbeat_loop, name=f"{self.settings.evaluator_node_id}-heartbeat", daemon=True),
            threading.Thread(target=self._poll_loop, name=f"{self.settings.evaluator_node_id}-poll", daemon=True),
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
                "evaluator_node_id": self.settings.evaluator_node_id,
                "registered": self.state.registered,
                "last_heartbeat_at": self.state.last_heartbeat_at.isoformat() if self.state.last_heartbeat_at else None,
                "current_task_id": self.state.current_task_id,
                "processed_tasks": self.state.processed_tasks,
                "last_error": self.state.last_error,
            }

    def ensure_registered(self) -> None:
        capabilities = None
        if self.settings.evaluator_capabilities_json:
            capabilities = json.loads(self.settings.evaluator_capabilities_json)
        self.orchestrator_client.register_node(
            node_id=self.settings.evaluator_node_id,
            endpoint_url=self.settings.evaluator_public_url,
            capabilities=capabilities,
        )
        with self._state_lock:
            self.state.registered = True
            self.state.last_error = None

    def heartbeat_once(self) -> None:
        try:
            if not self.state.registered:
                self.ensure_registered()
            self.orchestrator_client.heartbeat(node_id=self.settings.evaluator_node_id)
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
            task = self.orchestrator_client.claim_task(evaluator_node_id=self.settings.evaluator_node_id)
            if task is None:
                return False
            with self._state_lock:
                self.state.current_task_id = task.evaluation_task_id
                self.state.last_error = None
            self.orchestrator_client.start_task(
                evaluation_task_id=task.evaluation_task_id,
                evaluator_node_id=self.settings.evaluator_node_id,
            )

            model_artifact_id = self._artifact_id_from_uri(task.target_model_artifact_uri)
            dataset_artifact_id = self._artifact_id_from_uri(task.dataset_artifact_uri)
            _, model_payload = self.orchestrator_client.get_artifact_content(artifact_id=model_artifact_id)
            _, dataset_payload = self.orchestrator_client.get_artifact_content(artifact_id=dataset_artifact_id)
            self.workspace.write_task_file(task.evaluation_task_id, "model-result.json", model_payload)
            self.workspace.write_task_file(task.evaluation_task_id, "evaluation-manifest.json", dataset_payload)

            artifacts = self.executor.execute(
                task=task,
                model_payload=model_payload,
                dataset_payload=dataset_payload,
            )
            self.workspace.write_task_file(task.evaluation_task_id, "evaluation-report.json", artifacts.report_payload)

            report_artifact = self.orchestrator_client.upload_artifact(
                kind="evaluation_report",
                name=f"{task.evaluation_task_id}-report.json",
                payload=artifacts.report_payload,
                mime_type="application/json",
                metadata={
                    "evaluator_node_id": self.settings.evaluator_node_id,
                    "accuracy": artifacts.metrics_json["accuracy"],
                    "accepted": artifacts.acceptance_decision,
                    "round_id": task.round_id,
                },
                job_id=task.job_id,
                task_id=task.evaluation_task_id,
            )
            self.orchestrator_client.complete_task(
                evaluation_task_id=task.evaluation_task_id,
                evaluator_node_id=self.settings.evaluator_node_id,
                report_artifact_id=report_artifact.artifact_id,
                metrics_json=artifacts.metrics_json,
                sample_count=artifacts.sample_count,
                acceptance_decision=artifacts.acceptance_decision,
                target_model_digest=artifacts.target_model_digest,
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
                        evaluation_task_id=current_task_id,
                        evaluator_node_id=self.settings.evaluator_node_id,
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
