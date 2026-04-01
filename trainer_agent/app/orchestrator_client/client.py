from __future__ import annotations

import base64
from typing import Any

import httpx

from shared.python.schemas import ArtifactRecord, TrainingTaskRecord


class OrchestratorClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def register_node(self, *, node_id: str, endpoint_url: str, capabilities: dict[str, Any] | None) -> dict[str, Any]:
        response = self._client.post(
            "/nodes/register",
            json={
                "node_id": node_id,
                "role": "trainer",
                "endpoint_url": endpoint_url,
                "capabilities": capabilities,
            },
        )
        response.raise_for_status()
        return response.json()

    def heartbeat(self, *, node_id: str) -> dict[str, Any]:
        response = self._client.post("/nodes/heartbeat", json={"node_id": node_id})
        response.raise_for_status()
        return response.json()

    def claim_task(self, *, trainer_node_id: str) -> TrainingTaskRecord | None:
        response = self._client.post("/trainer/tasks/claim", json={"trainer_node_id": trainer_node_id})
        response.raise_for_status()
        payload = response.json()
        if payload is None:
            return None
        return TrainingTaskRecord.model_validate(payload)

    def start_task(self, *, task_id: str, trainer_node_id: str) -> TrainingTaskRecord:
        response = self._client.post(f"/trainer/tasks/{task_id}/start", json={"trainer_node_id": trainer_node_id})
        response.raise_for_status()
        return TrainingTaskRecord.model_validate(response.json())

    def complete_task(
        self,
        *,
        task_id: str,
        trainer_node_id: str,
        result_artifact_id: str,
        report_artifact_id: str,
    ) -> TrainingTaskRecord:
        response = self._client.post(
            f"/trainer/tasks/{task_id}/complete",
            json={
                "trainer_node_id": trainer_node_id,
                "result_artifact_id": result_artifact_id,
                "report_artifact_id": report_artifact_id,
            },
        )
        response.raise_for_status()
        return TrainingTaskRecord.model_validate(response.json())

    def fail_task(self, *, task_id: str, trainer_node_id: str, failure_reason: str) -> TrainingTaskRecord:
        response = self._client.post(
            f"/trainer/tasks/{task_id}/fail",
            json={"trainer_node_id": trainer_node_id, "failure_reason": failure_reason},
        )
        response.raise_for_status()
        return TrainingTaskRecord.model_validate(response.json())

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
        response = self._client.post(
            "/artifacts/upload",
            json={
                "kind": kind,
                "name": name,
                "payload_base64": base64.b64encode(payload).decode("utf-8"),
                "mime_type": mime_type,
                "metadata": metadata,
                "job_id": job_id,
                "task_id": task_id,
            },
        )
        response.raise_for_status()
        return ArtifactRecord.model_validate(response.json())

    def get_artifact_content(self, *, artifact_id: str) -> tuple[str, bytes]:
        response = self._client.get(f"/artifacts/{artifact_id}/content")
        response.raise_for_status()
        payload = response.json()
        return payload["mime_type"], base64.b64decode(payload["payload_base64"].encode("utf-8"))
