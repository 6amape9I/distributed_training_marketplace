from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ArtifactRef(BaseModel):
    artifact_id: str | None = None
    uri: str
    digest: str | None = None


class ArtifactRecord(BaseModel):
    artifact_id: str
    kind: str
    uri: str
    content_hash: str
    content_size_bytes: int = Field(ge=0)
    mime_type: str
    metadata_json: dict[str, Any] | None = None
    job_id: int | None = None
    task_id: str | None = None
    created_at: datetime | None = None
