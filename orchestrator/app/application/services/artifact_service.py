from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from orchestrator.app.domain.entities import Artifact
from orchestrator.app.domain.enums import ArtifactKind
from orchestrator.app.domain.repositories import ArtifactRepository
from orchestrator.app.infrastructure.storage.local_filesystem import LocalFilesystemStorage
from shared.python.hashing import digest_bytes


class ArtifactNotFoundError(LookupError):
    pass


class ArtifactService:
    def __init__(self, repository: ArtifactRepository, storage: LocalFilesystemStorage) -> None:
        self.repository = repository
        self.storage = storage

    def upload(
        self,
        *,
        kind: ArtifactKind,
        name: str,
        payload: bytes,
        mime_type: str,
        metadata: dict[str, object] | None = None,
        job_id: int | None = None,
        task_id: str | None = None,
    ) -> Artifact:
        artifact_id = f"artifact-{uuid4().hex}"
        digest = digest_bytes(payload)
        relative_path = self.storage.save_bytes(artifact_id=artifact_id, name=name, payload=payload)
        artifact = Artifact(
            artifact_id=artifact_id,
            kind=kind,
            uri=f"artifact://{artifact_id}",
            content_hash=digest,
            content_size_bytes=len(payload),
            mime_type=mime_type,
            metadata_json={**(metadata or {}), "storage_path": str(relative_path)},
            job_id=job_id,
            task_id=task_id,
        )
        return self.repository.upsert(artifact)

    def upload_base64(
        self,
        *,
        kind: ArtifactKind,
        name: str,
        payload_base64: str,
        mime_type: str,
        metadata: dict[str, object] | None = None,
        job_id: int | None = None,
        task_id: str | None = None,
    ) -> Artifact:
        return self.upload(
            kind=kind,
            name=name,
            payload=base64.b64decode(payload_base64.encode("utf-8")),
            mime_type=mime_type,
            metadata=metadata,
            job_id=job_id,
            task_id=task_id,
        )

    def get(self, artifact_id: str) -> Artifact:
        artifact = self.repository.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(f"artifact not found: {artifact_id}")
        return artifact

    def read_content(self, artifact_id: str) -> bytes:
        artifact = self.get(artifact_id)
        metadata = artifact.metadata_json or {}
        storage_path = metadata.get("storage_path")
        if not isinstance(storage_path, str):
            raise ArtifactNotFoundError(f"artifact storage path missing: {artifact_id}")
        return self.storage.load_bytes(Path(storage_path))
