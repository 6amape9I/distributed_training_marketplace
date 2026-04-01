from __future__ import annotations

from typing import Any, Protocol

from shared.python.schemas import ArtifactRecord, TrainingTaskRecord


class OrchestratorClientProtocol(Protocol):
    def register_node(self, *, node_id: str, endpoint_url: str, capabilities: dict[str, Any] | None) -> dict[str, Any]: ...

    def heartbeat(self, *, node_id: str) -> dict[str, Any]: ...

    def claim_task(self, *, trainer_node_id: str) -> TrainingTaskRecord | None: ...

    def start_task(self, *, task_id: str, trainer_node_id: str) -> TrainingTaskRecord: ...

    def complete_task(
        self,
        *,
        task_id: str,
        trainer_node_id: str,
        result_artifact_id: str,
        report_artifact_id: str,
    ) -> TrainingTaskRecord: ...

    def fail_task(self, *, task_id: str, trainer_node_id: str, failure_reason: str) -> TrainingTaskRecord: ...

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
