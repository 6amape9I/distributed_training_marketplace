from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from orchestrator.app.domain.enums import ArtifactKind


class ArtifactUploadRequest(BaseModel):
    kind: ArtifactKind
    name: str = Field(min_length=1, max_length=255)
    payload_base64: str = Field(min_length=1)
    mime_type: str = Field(min_length=1, max_length=255)
    metadata: dict[str, Any] | None = None
    job_id: int | None = None
    task_id: str | None = None


class ArtifactResponse(BaseModel):
    artifact_id: str
    kind: str
    uri: str
    content_hash: str
    content_size_bytes: int
    mime_type: str
    metadata_json: dict[str, Any] | None = None
    job_id: int | None = None
    task_id: str | None = None
    created_at: datetime | None = None


class ArtifactContentResponse(BaseModel):
    artifact_id: str
    mime_type: str
    payload_base64: str
