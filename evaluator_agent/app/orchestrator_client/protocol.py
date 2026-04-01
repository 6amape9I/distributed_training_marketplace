from __future__ import annotations

from typing import Any, Protocol

from shared.python.schemas import ArtifactRecord, EvaluationTaskRecord


class OrchestratorClientProtocol(Protocol):
    def register_node(self, *, node_id: str, endpoint_url: str, capabilities: dict[str, Any] | None) -> dict[str, Any]: ...

    def heartbeat(self, *, node_id: str) -> dict[str, Any]: ...

    def claim_task(self, *, evaluator_node_id: str) -> EvaluationTaskRecord | None: ...

    def start_task(self, *, evaluation_task_id: str, evaluator_node_id: str) -> EvaluationTaskRecord: ...

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
    ) -> EvaluationTaskRecord: ...

    def fail_task(
        self,
        *,
        evaluation_task_id: str,
        evaluator_node_id: str,
        failure_reason: str,
    ) -> EvaluationTaskRecord: ...

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
    ) -> ArtifactRecord: ...

    def get_artifact_content(self, *, artifact_id: str) -> tuple[str, bytes]: ...
