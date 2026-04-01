from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestrator.app.domain.enums import ArtifactKind


@dataclass(slots=True, frozen=True)
class Artifact:
    artifact_id: str
    kind: ArtifactKind
    uri: str
    content_hash: str
    content_size_bytes: int
    mime_type: str
    metadata_json: dict[str, Any] | None = None
    job_id: int | None = None
    task_id: str | None = None
    created_at: datetime | None = None
